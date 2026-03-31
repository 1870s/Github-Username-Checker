@echo off
echo ==========================================
echo    GitHub Username Checker - BUILD
echo ==========================================
echo.

REM Locate pyinstaller
set PYINST=%APPDATA%\Python\Python314\Scripts\pyinstaller.exe
if not exist "%PYINST%" (
    set PYINST=pyinstaller
)

echo Building exe...
"%PYINST%" --onefile --windowed --name "GithubUsernameChecker" --clean main.py

echo.
if exist "dist\GithubUsernameChecker.exe" (
    echo ✓ Build erfolgreich!
    echo   → dist\GithubUsernameChecker.exe
) else (
    echo ✗ Build fehlgeschlagen.
)
pause
