import argparse
import cv2
import numpy as np
import os
import onnx
import onnxruntime
import sys
import time
import torch
import pdb


CUR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CUR))

from utils import read_points, keep_bbox_from_lidar_range, vis_pc
from model import PointPillarsPre, PointPillarsPos


def point_range_filter(pts, point_range=[0, -39.68, -3, 69.12, 39.68, 1]):
    '''
    data_dict: dict(pts, gt_bboxes_3d, gt_labels, gt_names, difficulty)
    point_range: [x1, y1, z1, x2, y2, z2]
    '''
    flag_x_low = pts[:, 0] > point_range[0]
    flag_y_low = pts[:, 1] > point_range[1]
    flag_z_low = pts[:, 2] > point_range[2]
    flag_x_high = pts[:, 0] < point_range[3]
    flag_y_high = pts[:, 1] < point_range[4]
    flag_z_high = pts[:, 2] < point_range[5]
    keep_mask = flag_x_low & flag_y_low & flag_z_low & flag_x_high & flag_y_high & flag_z_high
    pts = pts[keep_mask]
    return pts 


def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


def main(args):
    CLASSES = {
        'Pedestrian': 0, 
        'Cyclist': 1, 
        'Car': 2
        }
    LABEL2CLASSES = {v:k for k, v in CLASSES.items()}
    pcd_limit_range = np.array([0, -40, -3, 70.4, 40, 0.0], dtype=np.float32)

    ## 1.1 onnx check and onnx load
    try:
        # 当我们的模型不可用时，将会报出异常
        onnx.checker.check_model(args.onnx_path)
    except onnx.checker.ValidationError as e:
        print("The model is invalid: %s"%e)
    else:
        # 模型可用时，将不会报出异常，并会输出“The model is valid!”
        print("The model is valid!")

    # sess = onnxruntime.InferenceSession('checkpoint/model.onnx')
    print('onnx version: ', onnxruntime.get_device())
    sess = onnxruntime.InferenceSession(args.onnx_path, providers=['CUDAExecutionProvider'])
    print(sess.get_providers())
    input_pillars_name = sess.get_inputs()[0].name
    input_coors_batch_name = sess.get_inputs()[1].name
    input_npoints_per_pillar_name = sess.get_inputs()[2].name
    output_name = sess.get_inputs()[0].name

    if not args.no_cuda:
        model_pre = PointPillarsPre().cuda()
        model_post = PointPillarsPos(nclasses=len(CLASSES)).cuda()
    else:
        model_pre = PointPillarsPre()
        model_post = PointPillarsPos(nclasses=len(CLASSES))
    
    if not os.path.exists(args.pc_path):
        raise FileNotFoundError 
    pc = read_points(args.pc_path)
    pc = point_range_filter(pc)
    pc_torch = torch.from_numpy(pc)

    model_pre.eval()
    model_post.eval()
    with torch.no_grad():
        if not args.no_cuda:
            pc_torch = pc_torch.cuda()
        pillars, coors_batch, npoints_per_pillar = model_pre(batched_pts=[pc_torch])
        input_data = {input_pillars_name: to_numpy(pillars),
                      input_coors_batch_name: to_numpy(coors_batch),
                      input_npoints_per_pillar_name: to_numpy(npoints_per_pillar)}
        result = sess.run(None, input_data)
        result = [torch.from_numpy(item).cuda() for item in result]
        result_filter = model_post(result)[0]
    result_filter = keep_bbox_from_lidar_range(result_filter, pcd_limit_range)
    lidar_bboxes = result_filter['lidar_bboxes']
    labels, scores = result_filter['labels'], result_filter['scores']
    vis_pc(pc, bboxes=lidar_bboxes, labels=labels)
    result_array = np.concatenate([lidar_bboxes, scores[:, None], labels[:, None]], axis=-1)
    os.makedirs(os.path.dirname(args.saved_path), exist_ok=True)
    np.savetxt(args.saved_path, result_array, fmt='%.4f')

    time_total, time_pre, time_model, time_post = 0.0, 0.0, 0.0, 0.0
    test_samples = 100
    start_total_time = time.time()
    for i in range(test_samples):
        with torch.no_grad():
            if not args.no_cuda:
                pc_torch = pc_torch.cuda()
            start_pre_time = time.time()
            pillars, coors_batch, npoints_per_pillar = model_pre(batched_pts=[pc_torch])
            end_pre_time = time.time()
            time_pre += (end_pre_time - start_pre_time)

            start_model_time = time.time()
            input_data = {input_pillars_name: to_numpy(pillars),
                        input_coors_batch_name: to_numpy(coors_batch),
                        input_npoints_per_pillar_name: to_numpy(npoints_per_pillar)}
            result = sess.run(None, input_data)
            result = [torch.from_numpy(item).cuda() for item in result]
            end_model_time = time.time()
            time_model += (end_model_time - start_model_time)

            start_post_time = time.time()
            result_filter = model_post(result)[0]
            result_filter = keep_bbox_from_lidar_range(result_filter, pcd_limit_range)
            end_post_time = time.time()
            time_post += (end_post_time - start_post_time)
    end_total_time = time.time()
    time_total = end_total_time - start_total_time

    avg_total_time = time_total * 1.0 / test_samples * 1000.0
    avg_pre_time = time_pre * 1.0 / test_samples * 1000.0
    avg_model_time = time_model * 1.0 / test_samples * 1000.0
    avg_post_time = time_post * 1.0 / test_samples * 1000.0
    print('ONNX total: {:.2f}ms, pre: {:.2f}ms, model: {:.2f}ms, post: {:.2f}ms'
          .format(avg_total_time, avg_pre_time, avg_model_time, avg_post_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Configuration Parameters')
    parser.add_argument('--pc_path', help='your point cloud path')
    parser.add_argument('--saved_path', default='infer_results/onnx.txt',
                        help='your saved path for comparision bewteen PyTorch, ONNX and TRT')
    parser.add_argument('--onnx_path', default='../pretrained/model.onnx',
                        help='your saved onnx path')
    parser.add_argument('--no_cuda', action='store_true',
                        help='whether to use cuda')
    args = parser.parse_args()

    main(args)
