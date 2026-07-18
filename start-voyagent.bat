@echo off
setlocal enabledelayedexpansion
title Voyagent Launcher

rem === Voyagent tek klik launcher ===
rem Docker Desktop-u qaldirir, konteynerleri ise salir, brauzeri acir.

cd /d "%~dp0"

echo.
echo   Voyagent baslatilir...
echo.

rem 1) Docker daemon isleyirmi?
docker info >nul 2>&1
if errorlevel 1 (
    echo   Docker Desktop islemir - baslatilir...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo   XETA: Docker Desktop tapilmadi. Elle acin ve yeniden cehd edin.
        pause
        exit /b 1
    )
    echo   Docker mexanizmi hazir olana qeder gozlenilir...
    set /a tries=0
    :waitdocker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 (
        set /a tries+=1
        if !tries! geq 40 (
            echo   XETA: Docker vaxtinda qalxmadi. Docker Desktop-u yoxlayin.
            pause
            exit /b 1
        )
        goto waitdocker
    )
)

echo   Docker hazirdir. Konteynerler qaldirilir (ilk defe bir qeder cekir)...
docker compose up -d --build
if errorlevel 1 (
    echo   XETA: docker compose ugursuz oldu. Yuxaridaki loga baxin.
    pause
    exit /b 1
)

echo   Frontend hazir olana qeder gozlenilir...
set /a wtries=0
:waitweb
timeout /t 2 /nobreak >nul
curl -s -o nul http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    set /a wtries+=1
    if !wtries! geq 30 (
        echo   XEBERDARLIQ: Frontend hele cavab vermir, yene de brauzer acilir.
        goto openweb
    )
    goto waitweb
)

:openweb
echo   Hazirdir! Brauzer acilir: http://localhost:8000
start "" http://localhost:8000
echo.
echo   Voyagent isleyir. Bu pencereni bagliya bilersiniz.
echo   Dayandirmaq ucun:  docker compose down
echo.
timeout /t 5 /nobreak >nul
exit /b 0
