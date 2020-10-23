#### 开机自启动
```
1. 打开文件夹
   C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp
2. 把软件的快捷方式，或是文件放到该启动文件夹中，Win10开机后就可以自动运行了。
```
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
##### 方法2：
1. instsrv.exe和srvany.exe使用全路径
   ```
   E:\BaiduNetdiskDownload\instsrv+srvany\instsrv.exe EtcPayService E:\BaiduNetdiskDownload\instsrv+srvany\srvany.exe
   ```
   
2. 双击 EtcPayService.reg 文件，导入注册表
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
   
