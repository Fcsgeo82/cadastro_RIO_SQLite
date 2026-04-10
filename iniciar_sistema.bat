@echo off
cd /d "c:\github_repositories\cadastro_RIO_SQLite"

echo ======================================================
echo    🚌 INICIANDO SISTEMA DE CADASTRO RIO (SQLITE)
echo ======================================================
echo.

:: 1. Inicia o Streamlit em uma nova janela
echo [1/2] Abrindo servidor Streamlit...
start "STREAMLIT SERVER" cmd /k "call venv\Scripts\activate && python -m streamlit run app.py"

:: Aguarda o servidor subir um pouco
timeout /t 5 /nobreak > nul

:: 2. Inicia o Tunel na janela atual para o usuário ver a URL
echo [2/2] Abrindo Tunel Pinggy (Porta 443)...
echo.
echo ------------------------------------------------------
echo  IMPORTANTE: Copie a URL 'https://...' que aparecer!
echo ------------------------------------------------------
echo.
ssh -o ServerAliveInterval=30 -p 443 -R 80:127.0.0.1:8501 free.pinggy.io

pause
