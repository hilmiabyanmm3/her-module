#!/usr/bin/env bash
echo "Starting HER Learning Module..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi
streamlit run Main_Menu.py
