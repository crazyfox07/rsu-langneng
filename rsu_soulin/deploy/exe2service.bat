:: 当前bat所在目录
set current_path=%cd%
:: 服务名称
set service_name=EtcPayService
:: exe所在目录
set prog_path=%current_path%\..
:: exe名称
set prog_name=main.exe
:: 注册服务
echo %current_path%\instsrv.exe %service_name% %current_path%\srvany.exe
ping -n 1 127.0.0.1>nul
%current_path%\instsrv.exe %service_name% %current_path%\srvany.exe

reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\%service_name%\Parameters" /v Application /t REG_SZ /d "%prog_path%\%prog_name%" /f
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\%service_name%\Parameters" /v AppDirectory /t REG_SZ /d "%prog_path%" /f
