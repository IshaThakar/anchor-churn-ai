@echo off
title Anchor - Predictive Intelligence for Customer Retention
echo =========================================================
echo Starting Anchor Retention Intelligence Platform...
echo =========================================================
py -3.13 run.py
if %ERRORLEVEL% NEQ 0 (
    python run.py
)
pause
