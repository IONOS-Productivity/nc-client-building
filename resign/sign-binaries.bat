@echo off
setlocal EnableDelayedExpansion

Rem ******************************************************************************************
rem 			"installer - collect files for Windows 64-bit and/or 32-bit"
Rem ******************************************************************************************

call "%~dp0/defaults.inc.bat" %1

Rem ******************************************************************************************

rem Reference: https://ss64.com/nt/setlocal.html
rem Reference: https://ss64.com/nt/start.html

Rem OpenSSL's libcrypto: Be future-proof! ;)
set "EXTRACT_PATH=C:/Daten/Resign/Extracted/PFiles/IONOS HiDrive Next"
echo "* EXTRACT_PATH=%EXTRACT_PATH%"

echo "* get libcrypto's dll filename from  %EXTRACT_PATH%"
start "get libcrypto's dll filename" /D "%EXTRACT_PATH%" /B /wait ls libcrypto-3*.dll > "%PROJECT_PATH%"/tmp
if %ERRORLEVEL% neq 0 goto onError
set /p LIBCRYPTO_DLL_FILENAME= < "%PROJECT_PATH%"\tmp
if %ERRORLEVEL% neq 0 goto onError
del "%PROJECT_PATH%"\tmp
echo "* LIBCRYPTO_DLL_FILENAME=%LIBCRYPTO_DLL_FILENAME%"


@REM echo "* copy %CRAFT_PATH%/bin/%LIBCRYPTO_DLL_FILENAME%."
@REM start "copy %LIBCRYPTO_DLL_FILENAME%" /D "%MY_COLLECT_PATH%/" /B /wait cp -af "%CRAFT_PATH%/bin/%LIBCRYPTO_DLL_FILENAME%" "%MY_COLLECT_PATH%/"
@REM if %ERRORLEVEL% neq 0 goto onError


Rem OpenSSL's libssl
echo "* get libssl's dll filename from %EXTRACT_PATH%"
start "get libssl's dll filename" /D "%EXTRACT_PATH%" /B /wait ls libssl-3*.dll > "%PROJECT_PATH%"/tmp
if %ERRORLEVEL% neq 0 goto onError
set /p LIBSSL_DLL_FILENAME= < "%PROJECT_PATH%"\tmp
if %ERRORLEVEL% neq 0 goto onError
del "%PROJECT_PATH%"\tmp
echo "* LIBSSL_DLL_FILENAME=%LIBSSL_DLL_FILENAME%"

if "%USE_CODE_SIGNING%" == "0" (
    echo "** Don't sign: Code signing is disabled by USE_CODE_SIGNING"
) else (
    echo "** Trying to find signtool in the PATH (VC env vars):"

    for %%i in (signtool.exe) do @set SIGNTOOL=%%~$PATH:i
    echo "* SIGNTOOL=%SIGNTOOL%"

    if "!SIGNTOOL!" == "" (
        echo "** Unable to find signtool.exe in the PATH."
        goto onError
    ) else (
        echo "** Found signtool.exe: !SIGNTOOL!"
    )

    echo "** Code signing begins:"

    for %%G in (
            "NCContextMenu.dll"
            "NCOverlays.dll"
            "%APP_NAME_SANITIZED%.exe"
            "%APP_NAME_SANITIZED%cmd.exe"
            "%APP_NAME_SANITIZED%sync.dll"
            "%APP_NAME_SANITIZED%_csync.dll"
            "qt6keychain%DLL_SUFFIX%.dll"
            "%LIBCRYPTO_DLL_FILENAME%"
            "%LIBSSL_DLL_FILENAME%"
            "zlib1%DLL_SUFFIX%.dll"
        ) do (

            echo "%EXTRACT_PATH%/%%~G"

            @REM @start "sign %%~G" /D "%PROJECT_PATH%/" /B /wait %~dp0/sign.bat "%EXTRACT_PATH%/%%~G"

            if !ERRORLEVEL! neq 0 goto onError
        )
    
    echo "** Code signing ends."
)

Rem ******************************************************************************************


exit 0

:testExit
echo "***** Test Exit! (%~nx0)"
exit 0
