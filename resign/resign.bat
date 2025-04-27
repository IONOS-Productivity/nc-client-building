@echo off
setlocal EnableDelayedExpansion
cls

echo "***** Resign started. (%~nx0)"

Rem ******************************************************************************************
rem 			"Build everything"
Rem ******************************************************************************************

call "%~dp0/defaults.inc.bat" %1 %2 %3

Rem ******************************************************************************************


Rem ******************************************************************************************
rem 			"check for required environment variables"
Rem ******************************************************************************************

call :testEnv PROJECT_PATH
call :testEnv BUILD_TYPE
call :testEnv BUILD_TARGETS
call :testEnv VS_VERSION
call :testEnv VCINSTALLDIR
call :testEnv WIN_GIT_PATH

if %ERRORLEVEL% neq 0 goto onError

echo "* USE_CODE_SIGNING=%USE_CODE_SIGNING%"
echo "* PROJECT_PATH=%PROJECT_PATH%"

Rem ******************************************************************************************
rem 			"collect files for the installer"
Rem ******************************************************************************************

echo "***** signing the binaries for the installer"
start "sign-binaries.bat" /D "%PROJECT_PATH%/" /B /wait "%~dp0/sign-binaries.bat"

if %ERRORLEVEL% neq 0 goto onError
goto testExit


Rem ******************************************************************************************
rem 			"build the installer"
Rem ******************************************************************************************


if "%BUILD_INSTALLER_MSI%" == "0" (
    echo "** Don't build the MSI installer (disabled by BUILD_INSTALLER_MSI)"
) else (
    echo "***** build the MSI installer."

    @REM start "build-installer-msi.bat %BUILD_TYPE%" /D "%PROJECT_PATH%/" /B /wait "%~dp0/build-installer-msi.bat" %BUILD_TYPE%
    start "single-build-installer-msi.bat %BUILD_TYPE% %%G" /D "%PROJECT_PATH%/" /B /wait "%~dp0/single-build-installer-msi.bat" %BUILD_TYPE% %BUILD_TARGETS%
)
if %ERRORLEVEL% neq 0 goto onError


Rem ******************************************************************************************

echo "***** Build finished. (%~nx0)"
exit 0

:onError
echo "***** Build FAILED! (%~nx0)"
if %ERRORLEVEL% neq 0 exit %ERRORLEVEL%
if !ERRORLEVEL! neq 0 exit !ERRORLEVEL!
exit 1

:testExit
echo "***** Test Exit! (%~nx0)"
exit 0

:testEnv
if "!%*!" == "" (
    echo "Missing environment variable: %*"
    exit /B 1
)
exit /B
