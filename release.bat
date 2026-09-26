@echo off
setlocal
cd /d "%~dp0"

echo Cleaning previous build artifacts...
py -m poetry run lovepack clean
if errorlevel 1 exit /b %errorlevel%

echo Building the wheel...
py -m poetry build --format wheel
if errorlevel 1 exit /b %errorlevel%

set "WHEEL="
for %%W in ("%~dp0dist\*.whl") do set "WHEEL=%%~fW"
if not defined WHEEL (
    echo ERROR: Poetry did not produce a wheel in dist\
    exit /b 1
)

echo Installing %WHEEL%...
py -m pip install --upgrade --force-reinstall "%WHEEL%"
if errorlevel 1 exit /b %errorlevel%

echo Done.
endlocal