@echo off
title TIR installer
echo -------------------------
cd ..
echo Building project...
echo -------------------------
python setup.py sdist
echo -------------------------
echo Terminating possible open driver instances
echo -------------------------
taskkill /f /im geckodriver.exe
taskkill /f /im chromedriver.exe
echo -------------------------
echo Installing project...
echo -------------------------
pip install -U dist/tir_framework-1.17.49.tar.gz
pause >nul | set/p = Press any key to exit ...