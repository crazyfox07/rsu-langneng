#### exe注册成服务
##### 方法1：
1. 以管理员的方式打开cmd，切换到deploy目录下
2. 运行exe2service.bat文件
3. 启动服务
   ```
   net start EtcPayService
   ```
4. 停止服务
   ```
   net stop EtcPayService
   ```
5. 删除服务
   ```
   方法一： sc delete EtcPayService
   方法二： E:\BaiduNetdiskDownload\instsrv+srvany\instsrv.exe EtcPayService remove
   ```
6. 查看服务
   ```
   运行 services.msc 打开服务查看器
   ```
##### windows中添加定时任务
1. [Win10下定时启动程序或脚本](https://blog.csdn.net/xielifu/article/details/81016220)
   
