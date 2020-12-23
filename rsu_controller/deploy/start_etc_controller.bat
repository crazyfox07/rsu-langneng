@echo off
:: =========日期时间按照YYYY-MM-DD HH:MM:SS格式显示=========
set CURRENT_HOUR=%time:~0,2%
echo %time%
echo %CURRENT_HOUR%
:: 5:00 启动服务， 22:00 暂停服务
if %CURRENT_HOUR% EQU 5 (
  net start EtcPayService
) else if %CURRENT_HOUR% EQU 22 (
  net stop EtcPayService
) else (
  echo "hello world"
)