# Tienda Jazmín — Sistema de inventario y ventas

Aplicación de escritorio para administrar el inventario, las ventas, los créditos a clientes y los reportes de una tienda. Está hecha en Python con **PySide6** (Qt) para la interfaz, **SQLite** como base de datos y **ReportLab** para generar PDF.

## Funcionalidades

| Sección | Qué permite hacer |
|---|---|
| **Inicio** | Resumen del día: productos activos, ventas de hoy, dinero recibido, crédito pendiente, stock bajo y últimas ventas |
| **Reportes** | Reportes diarios, semanales, mensuales y anuales con gráficos, comparación con el período anterior y exportación a PDF |
| **Ventas** | Registro de ventas al contado (efectivo, tarjeta u otro) o a crédito, con descuento automático del inventario |
| **Créditos** | Cuentas por cobrar: pagos parciales o totales, estado calculado (Pendiente / Parcial / Pagado), saldo por cliente y comprobante en PDF |
| **Inventario** | Entradas y salidas manuales, historial de movimientos y alertas de stock bajo |
| **Productos** | Alta, edición y activación/desactivación de productos con precios, existencia y stock mínimo |
| **Categorías** | Gestión de categorías de productos |
| **Clientes** | Registro de clientes con límite de crédito opcional |

Además:

- Inicio de sesión con contraseñas cifradas (PBKDF2-SHA256) y roles `admin` / `vendedor`.
- Búsqueda en todas las tablas sin importar mayúsculas ni tildes.
- Las consultas pesadas y la generación de PDF se ejecutan en segundo plano para no congelar la interfaz.

## Requisitos

- Python 3.10 o superior (probado con 3.13)
- Windows recomendado (el acceso directo y el icono de la barra de tareas son específicos de Windows), aunque la aplicación funciona en cualquier sistema compatible con PySide6.

## Instalación

Con `pip`:

```bash
python -m venv .venv
.venv\Scripts\activate          # En Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

O con [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.13
uv pip install --python .venv -r requirements.txt
```

## Ejecución

```bash
python main.py
```

Al abrir el sistema por primera vez:

1. Se crea la base de datos `database/tienda_jazmin.db` a partir de `database/schema.sql` (y se aplican las migraciones pendientes).
2. Si no existe ningún usuario, se crea un administrador por defecto:

   | Usuario | Contraseña |
   |---|---|
   | `admin` | `admin123` |

   **Cambia esta contraseña antes de usar el sistema en producción.**

### Acceso directo en el escritorio (Windows)

Con el entorno `.venv` ya creado, ejecuta desde la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\crear_acceso_directo.ps1
```

Se crea el acceso **Tienda Jazmín** en el escritorio, que abre el programa sin ventana de consola. Si mueves la carpeta del proyecto, vuelve a ejecutar el script.

## Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+1` … `Ctrl+8` | Cambiar de sección (en el orden del menú lateral) |
| `F5` | Recargar los datos de la pantalla actual |
| `Ctrl+Enter` | Guardar en los formularios |
| Doble clic en una fila | Editar el registro o abrir su detalle |

## Estructura del proyecto

```
├── main.py                 Punto de entrada
├── requirements.txt
├── crear_acceso_directo.ps1
├── tienda_jazmin.ico
├── database/               Conexión SQLite, esquema y migraciones
├── models/                 Acceso a datos (consultas SQL)
├── controllers/            Lógica de negocio y validaciones
├── helpers/                Formato, seguridad (hash de contraseñas) y sesión
├── reportes/               Períodos, resúmenes y generación de PDF
├── ui/                     Interfaz PySide6
│   ├── app.py              Arranque: login → ventana principal → cerrar sesión
│   ├── main_window.py      Barra superior, menú lateral y pantallas
│   ├── theme.py            Colores y tamaños
│   ├── styles/theme.qss    Estilos visuales
│   ├── pages/              Una pantalla por sección
│   ├── dialogs/            Formularios modales
│   └── widgets/            Componentes reutilizables (tablas, gráficos, avisos…)
└── views/                  Interfaz anterior en Tkinter (ya no se usa)
```

La aplicación sigue una separación en capas: **ui → controllers → models → database**. La interfaz nunca consulta la base de datos directamente.

## Base de datos

- Motor: SQLite 3, archivo `database/tienda_jazmin.db`.
- Tablas principales: `usuarios`, `categorias`, `productos`, `clientes`, `proveedores`, `ventas`, `detalle_ventas`, `compras`, `detalle_compras`, `pagos`, `movimientos_cuenta_cliente` y `movimientos_inventario`.
- **Todos los montos se guardan como enteros en centavos** (por ejemplo, $17.50 se guarda como `1750`) para evitar errores de redondeo.
- Las migraciones se aplican automáticamente al iniciar (`database/conexion.py`).
- El saldo, lo pagado y el estado de cada crédito no se guardan: se calculan siempre a partir de los pagos registrados.

Para crear o actualizar la base de datos sin abrir la interfaz:

```bash
python -m database.conexion
```

## Documentación adicional

[CAMBIOS_INTERFAZ.md](CAMBIOS_INTERFAZ.md) describe con más detalle la migración de Tkinter a PySide6, el módulo de reportes (de dónde sale cada dato) y el funcionamiento de los créditos.
