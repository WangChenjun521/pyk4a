## install K4A 
```
git clone --recursive https://github.com/microsoft/Azure-Kinect-Sensor-SDK.git

或者用ssh
git@github.com:microsoft/Azure-Kinect-Sensor-SDK.git

# 拉取tag 1.4.1 版本
git checkout tags/v1.4.1 -b v1.4.1

## mkdir -p /etc/udev/rules.d

cp ./scripts/99-k4a.rules /etc/udev/rules.d/

mkdir build && cd build

pip install Ninja

cmake .. -GNinja

```

#官方教程


https://github.com/microsoft/Azure-Kinect-Sensor-SDK/blob/develop/docs/depthengine.md


https://learn.microsoft.com/en-us/azure/kinect-dk/body-sdk-download

https://learn.microsoft.com/en-us/linux/packages

https://blog.csdn.net/sinat_37167645/article/details/120537631?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522169019256416800215016178%2522%252C%2522scm%2522%253A%252220140713.130102334.pc%255Fall.%2522%257D&request_id=169019256416800215016178&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~first_rank_ecpm_v1~rank_v31_ecpm-2-120537631-null-null.142^v91^control_2,239^v3^control&utm_term=ubuntu%2018.04%E5%AE%89%E8%A3%85kinect%20v1.4.1&spm=1018.2226.3001.4449

