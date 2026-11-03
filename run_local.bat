@echo off
title KMS Tu Vi - Local Launcher
echo ==============================================
echo     KHOI DONG KMS TU VI TREN MAY CUC BO (LOCAL)
echo ==============================================
echo.

set KMS_API_BASE=http://127.0.0.1:8000

echo [1/2] Dang khoi dong Backend FastAPI tai http://127.0.0.1:8000 ...
start "KMS Tu Vi - Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 >nul

echo [2/2] Dang khoi dong Frontend Streamlit tai http://127.0.0.1:8501 ...
start "KMS Tu Vi - Frontend" cmd /k "set KMS_API_BASE=http://127.0.0.1:8000 && python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false"

echo.
echo He thong dang chay! Ban co the truy cap:
echo -> Frontend: http://127.0.0.1:8501
echo -> Backend API Docs: http://127.0.0.1:8000/docs
echo.
pause

