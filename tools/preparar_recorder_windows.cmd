@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo.
echo  GROOVE RECORDER - PREPARADOR DE PRUEBA (NO VALIDADO EN SWITCH)
echo  -----------------------------------------------------------
echo  Solo para Groove 1.0.0 y emuMMC con copia de seguridad.
echo  Esta herramienta no instala ni modifica archivos de tu Switch.
echo.
if not exist "subsdk1" (
  echo ERROR: Falta subsdk1 en esta carpeta.
  pause
  exit /b 1
)
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3 no esta disponible mediante "py".
  echo Instala Python 3 o ejecuta build_recorder_lab_zip.py manualmente.
  pause
  exit /b 1
)
set "ORIGINAL=%~1"
if not defined ORIGINAL (
  echo Arrastra el main.npdm ORIGINAL del juego sobre este .cmd
  echo o introduce su ruta completa. El archivo main debe estar al lado.
  set /p "ORIGINAL=Ruta original main.npdm: "
)
set "ORIGINAL=%ORIGINAL:"=%"
if not exist "%ORIGINAL%" (
  echo ERROR: No existe el archivo indicado.
  pause
  exit /b 1
)
set "SDROOT="
echo.
set /p "SDROOT=Raiz de la SD para comprobar conflictos (por ejemplo E:\): "
set "SDROOT=%SDROOT:"=%"
if not defined SDROOT (
  echo ERROR: Es necesario comprobar la SD antes de preparar la prueba.
  pause
  exit /b 1
)
if "%SDROOT:~-1%"==":" set "SDROOT=%SDROOT%\"
set "OUT=%~dp0GrooveRecorder-LAB.zip"
if exist "%OUT%" (
  echo ERROR: Ya existe GrooveRecorder-LAB.zip. Guardalo antes de repetir.
  pause
  exit /b 1
)
choice /c SN /n /m "Preparar prueba de laboratorio sin validacion en Switch [S/N]? "
if errorlevel 2 exit /b 1
if not errorlevel 1 exit /b 1
py -3 "%~dp0build_recorder_lab_zip.py" "%ORIGINAL%" "%~dp0subsdk1" "%OUT%" --lab-ack --sd-root "%SDROOT%\."
if errorlevel 1 (
  echo.
  echo ERROR: Preparacion cancelada o validacion no superada.
  pause
  exit /b 1
)
echo.
echo Archivo experimental generado: "%OUT%"
echo AVISO: Este zip NO se ha probado en hardware. NO sustituir otros mods.
echo Lee README.md antes de considerar cualquier prueba en Switch.
pause
