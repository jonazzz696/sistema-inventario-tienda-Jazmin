# Crea un acceso directo "Tienda Jazmin" en el escritorio.
# El acceso abre el sistema con el Python del entorno .venv, sin ventana de consola.
#
# Uso (desde la carpeta del proyecto):
#   powershell -ExecutionPolicy Bypass -File .\crear_acceso_directo.ps1
#
# Si mueves la carpeta del proyecto, vuelve a ejecutar este script.

$carpeta = $PSScriptRoot
$pythonw = Join-Path $carpeta ".venv\Scripts\pythonw.exe"
$main    = Join-Path $carpeta "main.py"
$icono   = Join-Path $carpeta "tienda_jazmin.ico"

if (-not (Test-Path $pythonw)) {
    Write-Host ""
    Write-Host "No se encontro el entorno virtual (.venv) en esta carpeta." -ForegroundColor Red
    Write-Host "Primero crealo con:  uv venv --python 3.13  y  uv pip install --python .venv PySide6"
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

$escritorio = [Environment]::GetFolderPath("Desktop")
$ruta = Join-Path $escritorio "Tienda Jazmin.lnk"

$shell  = New-Object -ComObject WScript.Shell
$acceso = $shell.CreateShortcut($ruta)
$acceso.TargetPath       = $pythonw
$acceso.Arguments        = "`"$main`""
$acceso.WorkingDirectory = $carpeta
$acceso.Description      = "Sistema de inventario Tienda Jazmin"
if (Test-Path $icono) { $acceso.IconLocation = "$icono,0" }
$acceso.Save()

Write-Host ""
Write-Host "Listo. Acceso directo creado en:" -ForegroundColor Green
Write-Host "  $ruta"
Write-Host ""
