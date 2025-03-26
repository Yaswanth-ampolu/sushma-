@echo off
echo Starting Spring Test App...
python main.py
if %ERRORLEVEL% neq 0 (
    echo Application exited with error code %ERRORLEVEL%
    pause
) 