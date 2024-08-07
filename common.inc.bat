Rem ******************************************************************************************
rem "common environment Variables"
Rem ******************************************************************************************

set "BUILD_ARCH=%~2"
set "CMAKE_GENERATOR=Ninja"

if "%CRAFT_PATH%" == "" ( set "CRAFT_PATH=C:\Craft64" )
if "%QT_PATH%" == "" ( set "QT_PATH=C:\Qt" )
if "%QT_BIN_PATH%" == "" ( set "QT_BIN_PATH=C:\Qt\5.15.2\msvc2019_64\bin" )
if "%QT_PREFIX%" == "" ( set "QT_PREFIX=C:\Qt" )

set "PATH=%CRAFT_PATH%\bin;%CRAFT_PATH%\dev-utils\bin;%PATH%"