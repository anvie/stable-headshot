@echo off

if not defined PYTHON (set PYTHON=python)
if not defined VENV_DIR (set "VENV_DIR=%~dp0%venv")


set ERROR_REPORTING=FALSE

mkdir tmp 2>NUL

%PYTHON% -c "" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :check_pip
echo Couldn't launch python
goto :show_stdout_stderr

:check_pip
%PYTHON% -mpip --help >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :start_venv
if "%PIP_INSTALLER_LOCATION%" == "" goto :show_stdout_stderr
%PYTHON% "%PIP_INSTALLER_LOCATION%" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :start_venv
echo Couldn't install pip
goto :show_stdout_stderr

:start_venv
if ["%VENV_DIR%"] == ["-"] goto :skip_venv
if ["%SKIP_VENV%"] == ["1"] goto :skip_venv

dir "%VENV_DIR%\Scripts\Python.exe" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :activate_venv

for /f "delims=" %%i in ('CALL %PYTHON% -c "import sys; print(sys.executable)"') do set PYTHON_FULLNAME="%%i"
echo Creating venv in directory %VENV_DIR% using python %PYTHON_FULLNAME%
%PYTHON_FULLNAME% -m venv "%VENV_DIR%" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :activate_venv
echo Unable to create venv in directory "%VENV_DIR%"
goto :show_stdout_stderr

:activate_venv
set PYTHON="%VENV_DIR%\Scripts\Python.exe"
echo venv %PYTHON%

setlocal enabledelayedexpansion

REM Download dependencies
set "file_names[0]=./extensions/sd-webui-controlnet/models/control_openpose-fp16.yaml"
set "urls[0]=https://huggingface.co/KorewaDes/basicmodel/raw/main/control_openpose-fp16.yaml"
set "file_names[1]=./extensions/sd-webui-controlnet/models/control_openpose-fp16.safetensors"
set "urls[1]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/control_openpose-fp16.safetensors"
set "file_names[2]=./models/Codeformer/codeformer-v0.1.0.pth"
set "urls[2]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/codeformer-v0.1.0.pth"
set "file_names[3]=./models/GFPGAN/detection_Resnet50_Final.pth"
set "urls[3]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/detection_Resnet50_Final.pth"
set "file_names[4]=./models/GFPGAN/GFPGANv1.4.pth"
set "urls[4]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/GFPGANv1.4.pth"
set "file_names[5]=./models/Stable-diffusion/basemodel.safetensors"
set "urls[5]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/basemodel.safetensors"
set "file_names[6]=./repositories/CodeFormer/weights/facelib/detection_Resnet50_Final.pth"
set "urls[6]=https://huggingface.co/KorewaDes/basicmodel/resolve/main/detection_Resnet50_Final.pth"

set i=0
:check_deps
if defined file_names[%i%] (
    if not exist "!file_names[%i%]!" (
        echo File !file_names[%i%]! does not exist, downloading from !urls[%i%]!...
        @REM powershell -command "& { (New-Object Net.WebClient).DownloadFile('!urls[%i%]!', '!file_names[%i%]!') }"
        powershell -command "Invoke-WebRequest -Uri !urls[%i%]! -OutFile !file_names[%i%]!"
    ) else (
        echo File !file_names[%i%]! already exists, skipping download.
    )
    set /a i+=1
    goto :check_deps
)


:skip_venv
if [%ACCELERATE%] == ["True"] goto :accelerate
goto :launch

:accelerate
echo Checking for accelerate
set ACCELERATE="%VENV_DIR%\Scripts\accelerate.exe"
if EXIST %ACCELERATE% goto :accelerate_launch

:launch
%PYTHON% launch.py %*
pause
exit /b

:accelerate_launch
echo Accelerating
%ACCELERATE% launch --num_cpu_threads_per_process=6 launch.py
pause
exit /b

:show_stdout_stderr

echo.
echo exit code: %errorlevel%

for /f %%i in ("tmp\stdout.txt") do set size=%%~zi
if %size% equ 0 goto :show_stderr
echo.
echo stdout:
type tmp\stdout.txt

:show_stderr
for /f %%i in ("tmp\stderr.txt") do set size=%%~zi
if %size% equ 0 goto :show_stderr
echo.
echo stderr:
type tmp\stderr.txt

:endofscript

echo.
echo Launch unsuccessful. Exiting.
pause
