
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

#### 2.3 BackBone - with dynamic convolution

![Alt text](https://github.com/hajni77/dynamic_pillars/blob/main/backbone.png)


