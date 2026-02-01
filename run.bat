@echo off
cd /d "%~dp0"
echo ========================================
echo   Challenge Raids Orientation - Setup
echo ========================================
echo.

echo Verification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou pas accessible.
    echo.
    echo Pour installer Python :
    echo 1. Allez sur : https://www.python.org/downloads/
    echo 2. Telechargez la derniere version de Python
    echo 3. IMPORTANT: Cochez "Add Python to PATH" lors de l'installation
    echo.
    echo Voulez-vous ouvrir le site de telechargement maintenant ? (O/N)
    set /p choice="Votre choix: "
    if /i "%choice%"=="O" (
        start https://www.python.org/downloads/
        echo Site ouvert dans votre navigateur.
    )
    echo.
    echo Relancez ce script apres avoir installe Python.
    pause
    exit /b 1
)

echo Verification de pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip non trouve. Installation de pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo ERREUR: Impossible d'installer pip automatiquement.
        echo Veuillez reinstaller Python avec pip inclus.
        pause
        exit /b 1
    )
    echo pip installe avec succes!
echo.

echo Installation des dependances Python...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo ERREUR: Installation des dependances echouee.
    echo Tentative d'installation sans cache...
    python -m pip install -r requirements.txt --no-cache-dir
    if %errorlevel% neq 0 (
        echo ERREUR: Installation definitivement echouee.
        echo Verifiez votre connexion internet et les permissions.
        pause
        exit /b 1
    )
)

echo Dependances installees avec succes!
echo.
echo Lancement de l'application...
streamlit run app.py
pause