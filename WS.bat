@echo off
REM Activar entorno virtual
@REM call .venv\Scripts\activate.bat

cd scripts

echo ==============================
echo Iniciando web scraping...
echo ==============================


set PYTHON=..\.venv\Scripts\python.exe

powershell -NoProfile -Command ^
  "$procs=@();" ^
  "$scripts=@('D_cubso.py');" ^
  "foreach($s in $scripts){ $procs += Start-Process '%PYTHON%' -ArgumentList $s -PassThru };" ^
  "Wait-Process -Id ($procs | Select-Object -ExpandProperty Id)"



echo ==============================
echo Web scraping finalizado
echo ==============================

pause