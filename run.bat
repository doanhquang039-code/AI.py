@echo off
:: ============================================================
:: run.bat - Khoi dong AI Virtual World
:: ============================================================

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

IF "%1"=="visual" (
    echo [AI] Starting Pygame Simulation...
    python main.py --mode visual --episodes %2
) ELSE IF "%1"=="train" (
    echo [AI] Starting Headless Training...
    python main.py --mode train --episodes %2
) ELSE IF "%1"=="compare" (
    echo [AI] Starting Q-Learning vs DQN Comparison...
    python main.py --mode compare --episodes %2
) ELSE IF "%1"=="dashboard" (
    echo [AI] Starting Web Dashboard at http://localhost:5000
    python main.py --mode dashboard
) ELSE (
    echo.
    echo  === AI Virtual World - Q-Learning and DQN ===
    echo.
    echo  Usage:
    echo    run.bat visual [episodes]     - Pygame simulation
    echo    run.bat train [episodes]      - Headless training
    echo    run.bat compare [episodes]    - Compare QL vs DQN
    echo    run.bat dashboard             - Web dashboard
    echo.
    echo  Examples:
    echo    run.bat visual 500
    echo    run.bat train 2000
    echo    run.bat compare 300
    echo.
)
