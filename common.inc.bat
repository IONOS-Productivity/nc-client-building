Rem ******************************************************************************************
rem "common environment Variables"
Rem ******************************************************************************************

set "BUILD_ARCH=%~2"
set "CMAKE_GENERATOR=Ninja"

if "%BUILD_ARCH%" == "Win32" ( set "CRAFT_PATH=c:\Craft64" )
if "%BUILD_ARCH%" == "Win32" ( set "PATH=%CRAFT_PATH%\bin;%CRAFT_PATH%\dev-utils\bin;%PATH%" )
if "%BUILD_ARCH%" == "Win32" ( set "QT_PATH=C:\Qt" )
if "%BUILD_ARCH%" == "Win32" ( set "QT_BIN_PATH=C:\Qt\5.15.2\msvc2019_64\bin" )
if "%BUILD_ARCH%" == "Win32" ( set "QT_PREFIX=C:\Qt" )

if "%BUILD_ARCH%" == "Win64" ( set "CRAFT_PATH=c:\Craft64" )
if "%BUILD_ARCH%" == "Win64" ( set "PATH=%CRAFT_PATH%\bin;%PATH%" )
if "%BUILD_ARCH%" == "Win64" ( set "QT_PATH=C:\Craft64" )
if "%BUILD_ARCH%" == "Win64" ( set "QT_BIN_PATH=C:\Craft64\bin" )
if "%BUILD_ARCH%" == "Win64" ( set "QT_PREFIX=C:\Craft64" )