# setup.ps1 - Script de instalación rápida para Lead Finder AI
# Uso: .\setup.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Lead Finder AI - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version
    Write-Host "  ✓ $pythonVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python no encontrado. Instala Python 3.10+ desde python.org" -ForegroundColor Red
    exit 1
}

# 2. Crear entorno virtual
Write-Host "[2/6] Creando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  → Entorno virtual ya existe, saltando..." -ForegroundColor Gray
} else {
    py -m venv venv
    Write-Host "  ✓ Entorno virtual creado" -ForegroundColor Green
}

# 3. Activar entorno virtual
Write-Host "[3/6] Activando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
Write-Host "  ✓ Entorno activado" -ForegroundColor Green

# 4. Instalar dependencias
Write-Host "[4/6] Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "  ✓ Dependencias instaladas" -ForegroundColor Green

# 5. Crear archivo de configuración
Write-Host "[5/6] Configurando entorno..." -ForegroundColor Yellow
if (Test-Path ".env.local") {
    Write-Host "  → .env.local ya existe, saltando..." -ForegroundColor Gray
} else {
    Copy-Item ".env.example" ".env.local"
    Write-Host "  ✓ .env.local creado (edítalo con tus API keys)" -ForegroundColor Green
}

# 6. Inicializar base de datos
Write-Host "[6/6] Inicializando base de datos..." -ForegroundColor Yellow
$env:FLASK_APP = "app.py"
flask init-db 2>$null
flask seed-demo 2>$null
Write-Host "  ✓ Base de datos inicializada con datos demo" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ¡Instalación completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar el servidor:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  flask run"
Write-Host ""
Write-Host "Luego abre: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login demo:" -ForegroundColor Yellow
Write-Host "  Email: demo@leadfinderai.com"
Write-Host "  Password: demo123456"
Write-Host ""
