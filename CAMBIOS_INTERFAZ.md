# Nueva interfaz PySide6 — Tienda Jazmín

## Cómo ejecutar

```
pip install -r requirements.txt
python main.py
```

Atajos: `Ctrl+1` … `Ctrl+7` cambian de sección, `F5` recarga los datos, `Ctrl+Enter` guarda en los formularios, y un doble clic en una fila la edita o abre su detalle.

## Qué cambió

**Interfaz (nuevo):** toda la carpeta `ui/`. Reemplaza a `views/` (Tkinter). `main.py` ahora arranca la interfaz nueva.

**Backend:** solo se **agregaron** dos archivos de lectura para la pantalla de Inicio. Ningún archivo existente de `models/`, `controllers/`, `helpers/` o `database/` fue modificado.

| Archivo nuevo | Qué hace |
|---|---|
| `models/estadisticas.py` | Consultas SELECT: productos activos, ventas de hoy, crédito pendiente |
| `controllers/controlador_dashboard.py` | Reúne esos datos + stock bajo + últimas ventas (funciones ya existentes) |

Tablas, columnas, consultas y funciones existentes: sin cambios.

**Carpeta `views/`:** ya no se usa. Se dejó intacta para poder comparar o volver atrás; se puede borrar cuando la nueva interfaz esté probada.

## Estructura de `ui/`

```
ui/
├── app.py                  arranque: login -> ventana principal -> cerrar sesión
├── main_window.py          barra superior + menú lateral + QStackedWidget
├── login_window.py
├── theme.py                colores y tamaños (cambiar el color principal aquí)
├── icons.py                iconos SVG propios (QtSvg, sin dependencias extra)
├── formato_ui.py           fechas y etiquetas de presentación
├── styles/theme.qss        TODOS los estilos visuales
├── pages/                  una pantalla por módulo
│   dashboard, ventas, creditos, inventario, productos, categorias, clientes
├── dialogs/                formularios modales
│   producto_dialog, cliente_dialog, historial_credito_dialog
└── widgets/                componentes reutilizables
    common (botones, tarjetas), data_table, forms, messages (diálogos + avisos),
    page (base de pantallas), form_dialog (base de formularios),
    sidebar, topbar, stat_card, responsive
```

## Qué pantalla usa qué función existente

| Pantalla | Funciones del controlador |
|---|---|
| Login | `controlador_login.iniciar_sesion` |
| Productos | `obtener_lista_productos`, `obtener_producto_por_id`, `registrar_producto`, `modificar_producto`, `alternar_estado_producto` |
| Categorías | `obtener_lista_categorias`, `registrar_categoria` |
| Inventario | `registrar_movimiento_manual`, `obtener_historial`, `obtener_productos_stock_bajo` |
| Clientes | `obtener_lista_clientes`, `obtener_cliente_por_id`, `registrar_cliente`, `modificar_cliente`, `alternar_estado_cliente` |
| Ventas | `obtener_productos_para_venta`, `registrar_venta`, `obtener_ventas_recientes` |
| Créditos | `obtener_clientes_con_saldo`, `obtener_historial_cliente` |

## Validaciones

Se conservan todas las del modelo y los controladores. La interfaz agrega comprobaciones previas solo para dar mensajes más claros y marcar en rojo el campo con problema:

- Producto: código, nombre, unidad y categoría obligatorios; **precio de venta mayor que 0** (regla nueva).
- Cliente: nombre y teléfono obligatorios; el límite de crédito solo acepta números con punto decimal.
- Cantidades y precios: los campos solo aceptan números válidos.

## Mejoras de uso que no cambian la lógica

- Búsqueda (sin importar mayúsculas ni tildes) y filtros en todas las tablas.
- Filtro por producto en el historial de inventario (usa el parámetro `id_producto` que `obtener_historial()` ya tenía).
- En Ventas, agregar un producto que ya está en el carrito suma la cantidad a su línea en lugar de crear otra.

## Problema detectado en el backend (no corregido)

En `models/venta.py`, si una venta trae **dos líneas del mismo producto**, cada línea calcula la existencia final desde la misma existencia inicial, y la segunda sobrescribe a la primera: solo se descuenta la última cantidad (ejemplo verificado: existencia 22, venta de 2 + 3, queda en 19 en lugar de 17). La pantalla anterior permitía que esto pasara. La nueva interfaz lo evita al unir las líneas, pero el modelo sigue aceptando esas listas.

---

# Módulo de Reportes

## Instalación

Requiere ReportLab para el PDF (ya está en `requirements.txt`):

```
uv pip install --python .venv -r requirements.txt
```

## Archivos nuevos

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Acceso a datos | `models/reportes.py` | Consultas SELECT filtradas por fecha en SQL |
| Lógica | `controllers/controlador_reportes.py` | Arma el reporte completo; lo usan la pantalla y el PDF |
| Lógica | `reportes/periodos.py` | Rangos diario / semanal (lunes a domingo) / mensual / anual, nombres de archivo |
| Lógica | `reportes/resumen.py` | Redacta el resumen del período con los datos reales |
| Lógica | `reportes/formato.py` | Formato de dinero, cantidades y fechas |
| PDF | `reportes/pdf.py` | Documento con ReportLab |
| Interfaz | `ui/pages/reportes.py` | Pantalla de Reportes |
| Interfaz | `ui/widgets/charts.py` | Gráficos de barras, ranking y dona (QPainter, sin dependencias) |
| Interfaz | `ui/widgets/tarea.py` | Consultas y PDF en segundo plano (QThread) |

Modificados: `ui/main_window.py` (nueva opción del menú), `ui/icons.py` (iconos nuevos),
`ui/widgets/common.py` (las tarjetas exponen su subtítulo), `requirements.txt`.
La base de datos no se modificó.

## De dónde sale cada dato

- **Ventas, ingresos, unidades vendidas, métodos de pago, ventas a crédito:** tablas `ventas` y `detalle_ventas`, sin contar ventas anuladas (`estado = 0`).
- **Entradas:** `movimientos_inventario` con `tipo = 'entrada'`.
- **Salidas manuales:** `movimientos_inventario` con `tipo = 'salida'` y **sin** `id_venta`. Cada venta también deja una salida en esa tabla; separarlas evita contar dos veces la misma operación.
- **Operaciones:** ventas + entradas + salidas manuales (+ ajustes, si algún día existen).
- **Stock bajo:** `existencia <= stock_minimo`. Es la situación **actual**; el sistema no guarda el stock histórico, así que no depende del período.
- **Comparación con el período anterior:** mismas consultas sobre el período inmediatamente anterior.
- **Abonos:** `movimientos_cuenta_cliente` con `tipo = 'abono'` (hoy siempre 0, porque aún no hay pantalla para registrar abonos).

## PDF

- Encabezado y pie en todas las páginas, "Página X de Y", fecha, hora y usuario que lo generó.
- Las tablas largas continúan en la página siguiente repitiendo su encabezado.
- El detalle de operaciones incluye como máximo las 500 más recientes (se indica cuántas había en total), para que un reporte anual no tenga cientos de páginas.
- Usa Segoe UI o Arial si están instaladas (Windows) y, si no, Helvetica.

---

# Créditos (cuentas por cobrar)

## Cómo funciona

1. **Venta a crédito** (desde Ventas, igual que antes): se registra la venta, se descuenta el inventario y se crea la deuda. El crédito queda **Pendiente**.
2. **Registrar pago** (Créditos → seleccionar → Registrar pago): se guarda el pago asociado a esa venta. No se crea otra venta ni se toca el inventario.
3. El **estado se calcula solo** a partir de los pagos: Pendiente (sin pagos), Parcial (con pagos y saldo), Pagado (saldo $0).

## Base de datos

No se creó ninguna tabla nueva. Se reutilizó la tabla `pagos`, que ya existía en el schema pero no se usaba, agregándole dos columnas con una migración automática en `database/conexion.py` (se ejecuta sola al abrir el sistema):

| Columna nueva | Para qué |
|---|---|
| `pagos.id_venta` | A qué crédito (venta a crédito) corresponde el pago |
| `pagos.metodo_pago` | Efectivo, tarjeta u otro |

Un **crédito es la venta a crédito original** (número de crédito = número de venta). Pagado, saldo y estado **no se guardan**: se calculan siempre desde los pagos, así nunca quedan desactualizados.

Cada pago se guarda en **una transacción**: el pago en `pagos` y el abono en `movimientos_cuenta_cliente`. Si algo falla, no se guarda nada. Por eso el saldo por cliente y el límite de crédito siguen funcionando igual que antes.

## Archivos

| Archivo | Cambio |
|---|---|
| `models/credito.py` | Nuevo: listado, detalle, registro de pagos, cobros por período |
| `controllers/controlador_creditos.py` | Se agregaron funciones (las anteriores siguen igual) |
| `reportes/comprobante.py` | Nuevo: PDF del estado del crédito |
| `ui/pages/creditos.py` | Pantalla renovada (dashboard, créditos por venta, saldo por cliente) |
| `ui/dialogs/pago_dialog.py`, `ui/dialogs/credito_detalle_dialog.py` | Nuevos |
| `database/conexion.py` | Migración de la tabla `pagos` |
| `models/estadisticas.py`, `ui/pages/dashboard.py` | "Ventas de hoy" muestra también lo recibido hoy |

## Ventas vs. dinero recibido (reportes)

| Concepto | Cálculo |
|---|---|
| Ventas totales | Todas las ventas del período (contado + crédito) |
| Ventas al contado | Ventas con efectivo, tarjeta u otro |
| Ventas a crédito | Ventas con método crédito (generan saldo por cobrar) |
| Cobros de créditos | Pagos recibidos en el período, **según la fecha del pago** |
| **Dinero recibido** | Ventas al contado + cobros de créditos |

Ejemplo verificado: venta a crédito de $500 en agosto, pago de $100 en agosto y $400 en septiembre. Agosto muestra $500 de venta y $100 recibidos; septiembre, $0 de venta y $400 recibidos; el año, una sola venta de $500 y $500 recibidos.
