@echo off
echo Setting up NEXUS Dashboard...

REM Install Python dependencies
pip install -r core\requirements.txt

REM Create necessary directories
mkdir config logs trading\logs instance 2>nul

REM Copy environment template
copy config\environment_template.env .env

echo Setup complete! Edit .env file and run: python core\main.py
pause
