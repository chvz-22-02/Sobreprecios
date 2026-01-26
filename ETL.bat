
@echo off
REM Activar entorno virtual
@REM call .venv\Scripts\activate.bat

cd scripts

echo ==============================
echo Lanzando procesos iniciales...
echo ==============================


set PYTHON=..\.venv\Scripts\python.exe

powershell -NoProfile -Command ^
  "$procs=@();" ^
  "$scripts=@('ci_adjudicaciones.py','ci_consorcio.py','ci_convocatorias.py','ci_entidades.py','ci_postor.py','ci_proveedores.py');" ^
  "foreach($s in $scripts){ $procs += Start-Process '%PYTHON%' -ArgumentList $s -PassThru };" ^
  "Wait-Process -Id ($procs | Select-Object -ExpandProperty Id)"



echo ==============================
echo Procesamientos iniciales finalizados.
echo Lanzando procesos finales...
echo ==============================

powershell -NoProfile -Command ^
  "$procs = @(); " ^
  "$scripts = @('D_detalle_postores.py','D_entidades.py','F_adjudicaciones.py','F_postores.py'); " ^
  "foreach($s in $scripts){ $procs += Start-Process '%PYTHON%' -ArgumentList $s -PassThru } ; " ^
  "Write-Host 'Esperando a que finalicen los procesos finales...'; " ^
  "Wait-Process -Id ($procs | Select-Object -ExpandProperty Id)"

echo ==============================
echo Todos los procesos han terminado.
echo ==============================
pause