## 0. Introduction

#### 0.1 Supported features
- [X] PyTorch2ONNX (Support dynamic axes)
- [X] ONNX2TRT (Support dynamic axes)
- [X] TRT Inference (Support dynamic axes)
- [X] Complete TRT/C++ detection pipline (including voxelizaion and post-processing)
- [X] Voxelization acceleration with CUDA
- [ ] Code unification with the main branch

#### 0.1 Performance


Similar detection results between PyTorch, ONNX and TRT inference are achieved. Detection results validated on val/000134.bin are summarized in `infer_results`. My experimental environment is as follows, (however, TensorRT >= 8 and the corresponding CUDA are recommend for supporting `ScatterND`)
- `GPU`: RTX 3080
- `CUDA`: 11.1
- `TensorRT`: 7.2.3.4

    |  | Voxelization (ms) | Inference (ms) | PostProcessing (ms) | Total (ms) |
    | :---: | :---: | :---: | :---: | :---: |
    | PyTorch | 5.78 (CUDA) | 17.15 | 4.45 |  27.39 |
    | ONNX | 5.66 (CUDA)| 15.82 | 2.64 | 24.13 |
    | TensorRT | 226.63 (C++) | 20.6 | 0 | 248.87 |
    | TensorRT(FP16) | 241.27 (C++) | 14.02 | 0 | 256.91 |
    | TensorRT | 5.07 (CUDA) | 18.15 | 0 | 24.56 |
    | TensorRT(FP16) | 5.11 (CUDA) | **12.15** | 0 | **18.51** |
    



## 1. PyTorch2ONNX

#### 1.1 PyTorch2ONNX

```
cd PointPillarsPointPillars/ops
python setup.py develop

cd PointPillars/deployment
python pytorch2onnx.py --ckpt ../pretrained/epoch_160.pth
```

#### 1.2 (Optional) ONNX inference

```
cd PointPillars/deployment
python onnx_infer.py --pc_path ../dataset/demo_data/val/000134.bin --onnx_path ../pretrained/model.onnx
```

#### 1.3 (Optional) Comaprison to Pytorch inference

```
cd PointPillars/deployment
python pytorch_infer.py --ckpt ../pretrained/epoch_160.pth --pc_path ../dataset/demo_data/val/000134.bin
```
## 2. ONNX2TRT
#### 2.1 ONNX2TRT
```
/your_path/TensorRT-7.2.3.4/bin/trtexec --onnx=../pretrained/model.onnx --saveEngine=../pretrained/model.trt \
--minShapes=input_pillars:200x32x4,input_coors_batch:200x4,input_npoints_per_pillar:200 \
--maxShapes=input_pillars:40000x32x4,input_coors_batch:40000x4,input_npoints_per_pillar:40000 \
--optShapes=input_pillars:5000x32x4,input_coors_batch:5000x4,input_npoints_per_pillar:5000
```

#### 2.2 TRT inference
```
cd PointPillars/deployment/trt_infer
mkdir build 
cd build
cmake ..
make

./trt_infer your_point_cloud_path your_trt_path
e.g. 
./trt_infer ../../../dataset/demo_data/val/000134.bin ../../../pretrained/model.trt
```
![Alt text](https://github.com/hajni77/dynamic_pillars/blob/main/backbone.png)


