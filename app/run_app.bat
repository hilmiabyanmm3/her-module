@echo off
title HER Streamlit Learning Module
echo Activating Virtual Environment...
call venv\Scripts\activate.bat 2>nul || (
    echo Creating python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)
streamlit run Main_Menu.py
pause
