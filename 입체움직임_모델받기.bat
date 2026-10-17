@echo off
cd /d "%~dp0"
echo Downloading depth model for 2.5D photo motion (Depth Anything V2 Small, 49.6MB, Apache-2.0)...
py -3.11 -X utf8 -c "import urllib.request,os;os.makedirs('models',exist_ok=True);d='models/depth_anything_v2_small_fp16.onnx';u='https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model_fp16.onnx';r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'});f=open(d+'.part','wb');s=urllib.request.urlopen(r,timeout=120);b=s.read(1<<20)
while b: f.write(b);b=s.read(1<<20)
f.close();os.replace(d+'.part',d);print('OK',os.path.getsize(d)//1000000,'MB')"
if errorlevel 1 (echo FAILED - check internet connection) else (echo Done. Photo 2.5D motion is now available.)
echo Downloading face detector for thumbnails (OpenCV YuNet, 230KB, Apache-2.0)...
py -3.11 -X utf8 -c "import urllib.request,os;os.makedirs('models',exist_ok=True);d='models/face_detection_yunet_2023mar.onnx';u='https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx';r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'});open(d,'wb').write(urllib.request.urlopen(r,timeout=120).read());print('OK',os.path.getsize(d)//1000,'KB')"
if errorlevel 1 (echo FAILED face model) else (echo Done. Thumbnails will keep text off faces.)
pause
