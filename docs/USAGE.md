# Guía de Uso - CADHY

Esta guía cubre las funcionalidades principales del addon CADHY para modelado de infraestructura hidráulica.

## Índice

- [Atajos de Teclado](#atajos-de-teclado)
- [Panel Principal](#panel-principal)
- [Flujo de Trabajo Básico](#flujo-de-trabajo-básico)
- [Configuración del Addon](#configuración-del-addon)
- [Logging y Depuración](#logging-y-depuración)

---

## Atajos de Teclado

CADHY incluye atajos de teclado para las operaciones más frecuentes. Todos funcionan en el **3D View**.

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| `Ctrl+Shift+B` | **Build Channel** | Construye el canal hidráulico desde la curva eje seleccionada |
| `Ctrl+Shift+U` | **Update Channel** | Actualiza un canal existente con nuevos parámetros |
| `Ctrl+Shift+D` | **Build CFD Domain** | Genera el dominio CFD (volumen de fluido) |
| `Ctrl+Shift+Alt+S` | **Generate Sections** | Genera cortes transversales a lo largo del canal |

### Requisitos para los Atajos

- Para `Build Channel` y `Build CFD Domain`: Debes tener una **curva** seleccionada o configurada como eje en el panel CADHY.
- Para `Update Channel`: Debes tener un **canal CADHY existente** seleccionado.
- Para `Generate Sections`: Debes tener un **eje configurado** con un canal creado.

### Personalizar Atajos

Puedes modificar los atajos desde:

1. `Edit > Preferences > Keymap`
2. Buscar "cadhy"
3. Modificar las combinaciones de teclas

---

## Panel Principal

El panel CADHY se encuentra en la **barra lateral del 3D View** (presiona `N` para mostrar/ocultar).

### Estructura de Paneles

```
CADHY
├── Main          → Configuración del canal y eje
├── CFD           → Dominio CFD y validación
├── Sections      → Generación de cortes
├── Export        → Exportar geometría y reportes
├── Render        → Materiales y configuración de render
└── Updates       → Actualizaciones del addon
```

### Panel Main

1. **Axis (Alignment)**: Selecciona la curva que define el eje del canal
2. **Section Type**: Trapezoidal, Rectangular o Circular
3. **Section Parameters**:
   - Bottom Width (ancho de solera)
   - Side Slope (talud H:V, solo trapezoidal)
   - Height (altura)
   - Freeboard (bordo libre)
   - Lining Thickness (espesor de revestimiento)
   - Resolution (resolución de muestreo en metros)

### Panel CFD

- **Generate CFD Domain**: Activa/desactiva generación de dominio
- **Inlet/Outlet Extension**: Extensiones para desarrollo de flujo
- **Water Level**: Nivel de agua en el canal
- **Fill Mode**: Nivel de agua o llenado completo

---

## Flujo de Trabajo Básico

### 1. Crear Canal Hidráulico

```
1. Crea una curva Bezier o Polyline (eje del canal)
2. Selecciona la curva
3. Configura parámetros en CADHY > Main
4. Presiona "Build Channel" o Ctrl+Shift+B
```

### 2. Generar Dominio CFD

```
1. Con el canal creado, ve a CADHY > CFD
2. Configura extensiones inlet/outlet
3. Establece nivel de agua
4. Presiona "Build CFD Domain" o Ctrl+Shift+D
5. Usa "Validate Mesh" para verificar watertight
```

### 3. Generar Secciones

```
1. Ve a CADHY > Sections
2. Configura intervalo (Step en metros)
3. Presiona "Generate Sections" o Ctrl+Shift+Alt+S
4. Exporta a CSV/JSON si es necesario
```

### 4. Exportar para CFD

```
1. Ve a CADHY > Export
2. Selecciona formato (STL/OBJ/PLY)
3. Configura ruta de exportación
4. Presiona "Export CFD Mesh"
```

---

## Configuración del Addon

Accede a las preferencias del addon desde:

```
Edit > Preferences > Add-ons > CADHY (expandir)
```

### Opciones Disponibles

#### Logging
| Opción | Descripción |
|--------|-------------|
| **Log Level** | Nivel de detalle: DEBUG, INFO, WARNING, ERROR |
| **Log to File** | Guarda logs en `~/.cadhy/cadhy.log` |
| **Max Log Files** | Número máximo de archivos de backup (rotación) |
| **Open Log File** | Abre el archivo de log en el editor de texto |

#### Developer
| Opción | Descripción |
|--------|-------------|
| **Developer Mode** | Activa funciones de desarrollo |
| **Show Debug Info** | Muestra información adicional en paneles |
| **Reload Add-on** | Recarga el addon sin reiniciar Blender |

#### CFD Integration
| Opción | Descripción |
|--------|-------------|
| **CFD Solver Path** | Ruta a solver CFD externo (ej. OpenFOAM) |

#### Defaults
| Opción | Descripción |
|--------|-------------|
| **Default Units** | Metros o Pies |
| **Default Export Format** | STL, OBJ o PLY |
| **Auto-Triangulate on Export** | Triangular automáticamente al exportar |

#### Updates
| Opción | Descripción |
|--------|-------------|
| **Auto-Check Updates** | Verificar actualizaciones al iniciar |
| **Update Channel** | Stable o Beta releases |

---

## Logging y Depuración

### Ubicación del Log

```
~/.cadhy/cadhy.log
```

- **Windows**: `C:\Users\<usuario>\.cadhy\cadhy.log`
- **macOS**: `/Users/<usuario>/.cadhy/cadhy.log`
- **Linux**: `/home/<usuario>/.cadhy/cadhy.log`

### Abrir Log desde Blender

1. `Edit > Preferences > Add-ons > CADHY`
2. Click en **"Open Log File"**

### Formato del Log

```
2026-01-03 14:30:45 - INFO - CADHY:42 - Starting: Build Channel
2026-01-03 14:30:46 - INFO - CADHY:48 - Completed: Build Channel (0.85s)
```

### Rotación de Logs

- Tamaño máximo por archivo: 500 KB
- Archivos de backup: 3 (configurable)
- Archivos: `cadhy.log`, `cadhy.log.1`, `cadhy.log.2`, `cadhy.log.3`

### Reportar Bugs

Cuando reportes un bug, incluye:

1. El archivo `~/.cadhy/cadhy.log`
2. Información del sistema (CADHY > Updates > Print System Info)
3. Pasos para reproducir el problema

---

## Indicadores de Progreso

Las operaciones largas muestran una barra de progreso en la parte inferior de Blender:

- **Build Channel**: Progreso durante muestreo de curva y construcción de mesh
- **Build CFD Domain**: Progreso durante generación y validación
- **Generate Sections**: Progreso por cada sección generada

---

## Feature Flags (Avanzado)

CADHY incluye un sistema de feature flags para habilitar/deshabilitar funcionalidades:

### Features Habilitadas por Defecto
- `core_channel`: Generación de canales
- `core_cfd`: Dominio CFD
- `core_sections`: Generación de secciones
- `core_export`: Exportación
- `blendergis_integration`: Integración con BlenderGIS (si está instalado)

### Features Experimentales (Deshabilitadas)
- `experimental_transitions`: Transiciones de sección A→B
- `experimental_bermas`: Bermas y canales compuestos
- `experimental_openfoam`: Exportación OpenFOAM

Para habilitar features experimentales (desde consola Python de Blender):

```python
from cadhy.core.util.features import features
features.enable("experimental_transitions")
```

---

## Próximos Pasos

- [Guía de Instalación](INSTALLATION.md)
- [Contribuir al Proyecto](../CONTRIBUTING.md)
- [Changelog](../CHANGELOG.md)
