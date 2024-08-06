@echo off
setlocal EnableDelayedExpansion
cls

echo "*** Build: desktop (%~nx0)"

Rem ******************************************************************************************
rem 			"environment Variables"
Rem ******************************************************************************************

call "%~dp0/common.inc.bat" %1 %2

Rem ******************************************************************************************

if "%TAG%" == "" set TAG=%TAG_DESKTOP%

set VERSION_SUFFIX=%VERSION_SUFFIX%-%BUILD_ARCH%

set MY_REPO=%PROJECT_PATH%/desktop
set MY_BUILD_PATH=%MY_REPO%/build
set MY_INSTALL_PATH=%PROJECT_PATH%/install/%BUILD_TYPE%/%BUILD_ARCH%
set MY_QT_DEPLOYMENT_PATH=%MY_INSTALL_PATH%/qt-libs

echo "* APP_NAME=%APP_NAME%"
echo "* USE_BRANDING=%USE_BRANDING%"
echo "* BUILD_TYPE=%BUILD_TYPE%"
echo "* BUILD_ARCH=%BUILD_ARCH%"
echo "* CMAKE_GENERATOR=%CMAKE_GENERATOR%"
echo "* CMAKE_EXTRA_FLAGS_DESKTOP=%CMAKE_EXTRA_FLAGS_DESKTOP%"
echo "* PROJECT_PATH=%PROJECT_PATH%"

echo "* QT_PREFIX=%QT_PREFIX%"
echo "* QT_PATH=%QT_PATH%"
echo "* QT_BIN_PATH=%QT_BIN_PATH%"

echo "* VCINSTALLDIR=%VCINSTALLDIR%"
echo "* Png2Ico_EXECUTABLE=%Png2Ico_EXECUTABLE%"

echo "* Build date %BUILD_DATE%"
echo "* VERSION_SUFFIX %VERSION_SUFFIX%"
echo "* TAG %TAG%"
echo "* PULL_DESKTOP %PULL_DESKTOP%"
echo "* CHECKOUT_DESKTOP %CHECKOUT_DESKTOP%"
echo "* BUILD_UPDATER %BUILD_UPDATER%"
echo "* BUILD_INSTALLER_MSI %BUILD_INSTALLER_MSI%"

echo "* MY_REPO=%MY_REPO%"
echo "* MY_BUILD_PATH=%MY_BUILD_PATH%"
echo "* MY_INSTALL_PATH=%MY_INSTALL_PATH%"
echo "* MY_QT_DEPLOYMENT_PATH=%MY_QT_DEPLOYMENT_PATH%"

echo "* PATH=%PATH%"

Rem ******************************************************************************************
rem 			"check for required environment variables"
Rem ******************************************************************************************

echo "* Check for required environment variables. 1"
call :testEnv APP_NAME
echo "* Check for required environment variables. 2"
call :testEnv PROJECT_PATH
echo "* Check for required environment variables. 3"
call :testEnv BUILD_TYPE
echo "* Check for required environment variables. 4"
call :testEnv BUILD_ARCH
echo "* Check for required environment variables. 5"
call :testEnv CMAKE_GENERATOR
echo "* Check for required environment variables. 6"
call :testEnv QT_PREFIX
echo "* Check for required environment variables. 7"
call :testEnv QT_PATH
echo "* Check for required environment variables. 8"
call :testEnv QT_BIN_PATH
echo "* Check for required environment variables. 9"
call :testEnv VCINSTALLDIR
echo "* Check for required environment variables. 10"
call :testEnv Png2Ico_EXECUTABLE
echo "* Check for required environment variables. 11"
call :testEnv BUILD_DATE
echo "* Check for required environment variables. 12"
call :testEnv BUILD_UPDATER
echo "* Check for required environment variables. 13"
call :testEnv TAG

if %ERRORLEVEL% neq 0 goto onError

if "%BUILD_ARCH%" == "Win64" ( call "%VCINSTALLDIR%\Auxiliary\Build\vcvarsall.bat" x64 )
if "%BUILD_ARCH%" == "Win32" ( call "%VCINSTALLDIR%\Auxiliary\Build\vcvarsall.bat" amd64_x86 )

Rem ******************************************************************************************
rem 			"Test run?"
Rem ******************************************************************************************

if "%TEST_RUN%" == "1" (
    echo "** TEST RUN - exit."
    exit
)

Rem ******************************************************************************************
rem 			"clean up"
Rem ******************************************************************************************

if "%SKIP_CLEANUP%" == "0" (
    echo "* Remove old installation files %MY_INSTALL_PATH% from previous build."
    start "rm -rf" /B /wait rm -rf "%MY_INSTALL_PATH%/"*
    if %ERRORLEVEL% neq 0 goto onError

    echo "* Remove old dependencies files %MY_QT_DEPLOYMENT_PATH% from previous build."
    start "rm -rf" /B /wait rm -rf "%MY_QT_DEPLOYMENT_PATH%/"*
    if %ERRORLEVEL% neq 0 goto onError

    echo "* Remove %MY_BUILD_PATH% from previous build."
    start "rm -rf" /B /wait rm -rf "%MY_BUILD_PATH%/"*
    if %ERRORLEVEL% neq 0 goto onError
) 

Rem ******************************************************************************************
rem 			"git pull, build, collect dependencies"
Rem ******************************************************************************************

rem Reference: https://ss64.com/nt/setlocal.html
rem Reference: https://ss64.com/nt/start.html

if "%PULL_DESKTOP%" == "1" (
    Rem Checkout master first to have it clean for git pull
    if "%CHECKOUT_DESKTOP%" == "1" (
        echo "* Remove %MY_REPO% from previous build."
        start "rm -rf" /B /wait rm -rf "%MY_REPO%/"
        if %ERRORLEVEL% neq 0 goto onError

        echo "* git checkout master at %MY_REPO%/."
        start "git checkout master" /B /wait git clone --depth=1 --branch=%TAG% https://github.com/nextcloud/client %MY_REPO%
    )
    if !ERRORLEVEL! neq 0 goto onError
) else (
    if "%CHECKOUT_DESKTOP%" == "1" (
        echo "* Remove %MY_REPO% from previous build."
        start "rm -rf" /B /wait rm -rf "%MY_REPO%/"*
        if %ERRORLEVEL% neq 0 goto onError

        echo "* git checkout %TAG% at %MY_REPO%/."
        start "git checkout %TAG%" /B /wait git clone --depth=1 --branch=%TAG% https://github.com/nextcloud/client %MY_REPO%
        if !ERRORLEVEL! neq 0 goto onError
    )
    if %ERRORLEVEL% neq 0 goto onError
)
if %ERRORLEVEL% neq 0 goto onError

echo "* Create desktop build directory"
start "mkdir %MY_BUILD_PATH%" /D "%PROJECT_PATH%/" /B /wait "%WIN_GIT_PATH%\usr\bin\mkdir.exe" -p "%MY_BUILD_PATH%"
if %ERRORLEVEL% neq 0 goto onError

echo "* save git HEAD commit hash from repo %MY_REPO%/."
start "git rev-parse HEAD" /D "%MY_REPO%/" /B /wait git rev-parse HEAD > "%PROJECT_PATH%"/tmp
if %ERRORLEVEL% neq 0 goto onError
set /p GIT_REVISION= < "%PROJECT_PATH%"\tmp
if %ERRORLEVEL% neq 0 goto onError
del "%PROJECT_PATH%"\tmp

echo "* Run cmake with CMAKE_INSTALL_PREFIX and CMAKE_BUILD_TYPE set at %MY_BUILD_PATH%."
echo "cmake -G%CMAKE_GENERATOR% .. -DMIRALL_VERSION_SUFFIX=%VERSION_SUFFIX% -DWITH_CRASHREPORTER=OFF -DBUILD_UPDATER=%BUILD_UPDATER% -DBUILD_WIN_MSI=%BUILD_INSTALLER_MSI% -DMIRALL_VERSION_BUILD=%BUILD_DATE% -DCMAKE_INSTALL_PREFIX=%MY_INSTALL_PATH% -DCMAKE_BUILD_TYPE=%BUILD_TYPE% -DCMAKE_PREFIX_PATH=%CRAFT_PATH% -DPng2Ico_EXECUTABLE=%Png2Ico_EXECUTABLE% %CMAKE_EXTRA_FLAGS_DESKTOP%"
start "cmake.." /D "%MY_BUILD_PATH%" /B /wait cmake "-G%CMAKE_GENERATOR%" .. -DMIRALL_VERSION_SUFFIX="%VERSION_SUFFIX%" -DWITH_CRASHREPORTER=OFF -DBUILD_UPDATER=%BUILD_UPDATER% -DBUILD_WIN_MSI=%BUILD_INSTALLER_MSI% -DMIRALL_VERSION_BUILD="%BUILD_DATE%" -DCMAKE_INSTALL_PREFIX="%MY_INSTALL_PATH%" -DCMAKE_BUILD_TYPE="%BUILD_TYPE%" -DCMAKE_PREFIX_PATH=%CRAFT_PATH% -DPng2Ico_EXECUTABLE="%Png2Ico_EXECUTABLE%" %CMAKE_EXTRA_FLAGS_DESKTOP%
if %ERRORLEVEL% neq 0 goto onError

echo "* Run cmake to compile and install."
start "cmake build" /D "%MY_BUILD_PATH%" /B /wait cmake --build . --config %BUILD_TYPE% --target install
if %ERRORLEVEL% neq 0 goto onError

if "%BUILD_TYPE%" == "Debug" (
    set WINDEPLOYQT_BUILD_TYPE=debug
) else (
    set WINDEPLOYQT_BUILD_TYPE=release
)
echo "* Run windeployqt to collect all %APP_NAME_EXE%.exe dependencies and output it to %MY_QT_DEPLOYMENT_PATH%/."
start "windeployqt" /B /wait %QT_BIN_PATH%/windeployqt.exe --%WINDEPLOYQT_BUILD_TYPE% --compiler-runtime "%MY_INSTALL_PATH%/bin/%APP_NAME_EXE%.exe" --dir "%MY_QT_DEPLOYMENT_PATH%/" --qmldir "%MY_REPO%/src/gui" -websockets
if %ERRORLEVEL% neq 0 goto onError

Rem ******************************************************************************************

echo "*** Finished Build: desktop %BUILD_TYPE% %BUILD_ARCH% (GIT_REVISION=%GIT_REVISION%) (%~nx0)"
exit 0

:onError
echo "*** Build FAILED: desktop %BUILD_TYPE% %BUILD_ARCH% (%~nx0)"
if %ERRORLEVEL% neq 0 exit %ERRORLEVEL%
if !ERRORLEVEL! neq 0 exit !ERRORLEVEL!
exit 1

:testEnv
if "!%*!" == "" (
    echo "Missing environment variable: %*"
    exit /B 1
)
exit /B
