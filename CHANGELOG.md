# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.5] - 2026-01-03

### Added

- **Triangular Section Type**: V-channel / triangular cross-section
  - Apex at bottom with configurable side slope
  - Full geometry and CFD domain support
  - Lining thickness support

- **Commercial Pipe Section Type**: Closed pipe with industry-standard dimensions
  - HDPE PE100 pipes (DN 110mm - 1200mm) with SDR 11/17
  - PVC pipes (2" - 24") with Schedule 40/80
  - Concrete pipes (DN 300mm - 2400mm)
  - Automatic wall thickness from standards
  - Full circle geometry for pressurized flow

- **Pipe Material Database**: Real commercial pipe specifications
  - Wall thickness calculated from SDR/Schedule
  - Inner diameter computed automatically
  - Standard nominal diameters

### Changed

- **CFD Domain Height**: Now uses full channel height (height + freeboard)
  - Previously only used design height, leaving gap at top
  - Ensures complete CFD simulation domain

- **Station Markers Position**: Text now positioned ABOVE the channel
  - Height offset based on channel height + freeboard
  - Inlet/Outlet markers include station text (e.g., "INLET\n0+000.00")
  - Duplicate station markers prevented

- **UI Section Parameters**: Dynamic display based on section type
  - Pipe mode shows material, diameter, SDR/Schedule
  - Triangular mode shows only side slope (no bottom width)
  - Calculated values display for each section type

### Fixed

- CFD domain not filling entire channel volume (freeboard gap)
- Station marker duplicates at curve endpoints
- Station text positioning below channel surface

---

## [0.3.4] - 2026-01-03

### Added

- **Pie Menu**: Quick access to all CADHY operations
  - Press `Alt+C` to open the pie menu
  - Context-aware buttons (shows "Update" vs "Build" based on selection)
  - 8 operations: Channel, CFD, Sections, Export, Markers, Report, Validate, Materials

- **Workspace Setup**: Optimized workspace for channel design
  - Creates "CADHY" workspace with engineering-friendly settings
  - Top-down view, metric units, solid shading with cavity
  - Stats overlay, vertex snapping enabled
  - Setup/Reset buttons in Updates panel

- **CFD Export Templates**: Pre-configured export for CFD solvers
  - OpenFOAM (snappyHexMesh, cfMesh)
  - ANSYS Fluent
  - STAR-CCM+
  - FLOW-3D
  - SimScale
  - Generic CFD
  - Auto-generates OpenFOAM dictionary files (blockMeshDict, snappyHexMeshDict)
  - Exports patches as separate STL files

- **Blender Extensions Platform Support**: Ready for Blender 4.2+
  - Added `blender_manifest.toml` with full metadata
  - Compatible with new Extensions repository

- **Presets System**: Save and load channel configurations
  - Built-in presets: Irrigation, Drainage, Culverts
  - Save custom presets for reuse
  - Presets menu in main panel

- **Help System**: Quick reference for shortcuts and features
  - Keyboard shortcuts viewer
  - Links to documentation

### Changed

- **Keyboard Shortcuts**: Changed to avoid conflicts with Blender defaults
  - `Alt+C`: CADHY Pie Menu
  - `Alt+Shift+B`: Build Channel
  - `Alt+Shift+U`: Update Channel
  - `Alt+Shift+D`: Build CFD Domain
  - `Alt+Shift+S`: Generate Sections

### Fixed

- Lint errors in build_channel.py (unused variables)
- Lint errors in op_presets.py (unused imports)

---

## [0.3.3] - 2026-01-03

### Fixed

- **Critical: Addon Registration Error**: Renamed `register.py` to `registration.py`
  - Fixed `'function' object has no attribute 'register'` error
  - Prevents name collision between module and function
  - Addon now loads correctly in Blender

- **CFD Domain BMesh Error**: Added `ensure_lookup_table()` after triangulation
  - Fixed `BMElemSeq[index]: outdated internal index table` crash

- **Cyclic Curve Geometry**: Fixed geometry crossing at closed curve corners
  - Detects cyclic splines and removes duplicate endpoint
  - Properly connects last section to first for closed loops

- **Channel Info Slope Format**: Removed confusing `1:N` slope format
  - Only shows slope as `%` and `m/m`

### Added

- **Parametric CFD Domain**: CFD domains now update with their source channel
  - New `CADHY_OT_UpdateCFDDomain` operator
  - CFD domain stores link to source channel
  - When channel is updated, linked CFD domains auto-update

- **Station Markers**: Visual chainage markers along the axis curve
  - Shows station in 0+000.00 format (km+meters)
  - INLET and OUTLET labels at endpoints
  - Create/Clear buttons in main panel

### Changed

- **CFD Domain Simplified**: Now follows channel geometry exactly
  - Removed Fill Mode option (always uses full channel height)
  - Removed inlet/outlet extensions (follows axis exactly)
  - Fluid volume matches channel precisely

---

## [0.3.2] - 2026-01-03

### Added

- **Channel Info Panel**: Real-time geometric and hydraulic information display
  - New collapsible panel "Channel Info" appears when a CADHY channel is selected
  - **Geometry Section**: Section type, bottom width, side slope, top width, heights
  - **Profile & Slope Section**: Channel length, slope (%, m/m, 1:N), elevation data
  - **Hydraulics Section**: 
    - Cross-sectional properties: Area, Wetted Perimeter, Hydraulic Radius
    - Manning's flow calculation: Velocity and Discharge at design depth
    - Editable Manning's n coefficient (default 0.015)
  - **Mesh Stats Section**: Vertices, edges, faces, triangles, volume, surface area
    - Manifold and watertight status indicators
    - Non-manifold edge count for debugging
  - "Refresh Info" button to recalculate all properties

- **Hydraulics Module**: New `cadhy/core/geom/hydraulics.py` with:
  - `HydraulicInfo`, `MeshStats`, `SlopeInfo` dataclasses
  - `get_curve_slope_info()`: Extract slope from curve axis
  - `get_mesh_stats()`: Calculate mesh statistics using bmesh
  - `calculate_hydraulic_info()`: Compute hydraulic properties
  - Support for TRAP, RECT, and CIRC sections

### Technical

- New panel `CADHY_PT_ChannelInfo` in `pt_channel_info.py`
- New operator `CADHY_OT_RefreshChannelInfo` for on-demand recalculation
- Extended `CADHYChannelSettings` with 20+ computed properties
- Stored properties for slope, hydraulics, and mesh stats on channel objects

---

## [0.3.1] - 2026-01-03

### Fixed

- **Critical: Update Channel Edit Mode Error**: Fixed `Cannot add vertices in edit mode` error
  - Channel updates now properly switch to object mode before modifying mesh
  - Allows repeated parameter changes without errors

- **Geometry Distortion at Curve Corners**: Implemented Rotation Minimizing Frames (RMF)
  - Previous approach caused section twisting at sharp corners (e.g., 90° bends)
  - New RMF algorithm propagates the normal along the curve smoothly
  - Eliminates geometry flipping and distortion at direction changes
  - Consistent section orientation throughout the entire channel

### Technical

- New `_sample_with_rmf()` function for consistent frame calculation
- New `_get_curve_polyline()` helper for curve vertex extraction
- New `_calculate_curvatures()` for curvature analysis
- Both uniform and adaptive sampling now use RMF for consistency

---

## [0.3.0] - 2026-01-03

### Added

- **AddonPreferences Panel**: Nueva configuración global accesible desde Edit > Preferences > Add-ons
  - Nivel de log configurable (DEBUG, INFO, WARNING, ERROR)
  - Opción de logging a archivo (~/.cadhy/cadhy.log)
  - Modo desarrollador con recarga de scripts
  - Path para solver CFD externo
  - Unidades por defecto y formato de exportación
  - Configuración de auto-updates

- **Enhanced Logging System**: Sistema de logging profesional similar a BlenderGIS
  - Rotación automática de archivos de log (máx 500KB, 3 backups)
  - Logs a ~/.cadhy/cadhy.log
  - Botón para abrir archivo de log desde preferencias
  - Timing de operaciones en logs

- **Global Exception Hook**: Captura automática de excepciones no manejadas
  - Las excepciones de CADHY se loggean automáticamente a archivo
  - Ayuda en debugging y reporte de bugs

- **Blender Version Validation**: Verificación de versión mínima al cargar
  - Error claro si Blender < 4.1.0

- **Keyboard Shortcuts**: Atajos de teclado para operaciones principales
  - Ctrl+Shift+B: Build Channel
  - Ctrl+Shift+U: Update Channel
  - Ctrl+Shift+D: Build CFD Domain
  - Ctrl+Shift+Alt+S: Generate Sections

- **Progress Indicators**: Indicadores de progreso para operaciones largas
  - Barra de progreso en Build Channel y CFD Domain
  - Mejor feedback visual durante generación de geometría

### Improved

- **PRD.md**: Documento limpiado y reestructurado
- **Code Architecture**: Mejor separación de responsabilidades
- **Error Handling**: Manejo de errores más robusto con logging automático

### Technical

- Nuevo archivo `cadhy/blender/preferences.py`
- Operador `CADHY_OT_OpenLogFile` para abrir logs
- Función `reconfigure_from_preferences()` para reconfigurar logging
- Keyboard shortcuts registrados en `register.py`

---

## [0.2.4] - 2026-01-03

### Improved
- **Optimized Release ZIP**: Smaller, cleaner addon package
  - Excluded `tests/` folder (not needed for addon functionality)
  - Excluded `README.md` and other markdown files
  - Excluded `.gitkeep` placeholder files
  - Reduced ZIP from ~58 files to ~49 files (100KB)

---

## [0.2.3] - 2026-01-03

### Fixed
- **Critical: Auto-Updater Installation Bug**: Fixed path calculation in `install_update()`
  - Previous version had wrong `dirname()` count causing incorrect addon directory detection
  - Could cause addon to disappear after update ("Missing Add-ons" in Blender)
  - Added safety checks to verify addon directory before operations
  - Added validation for ZIP structure and `__init__.py` presence
  - Improved backup/restore logic with proper error handling

---

## [0.2.2] - 2026-01-03

### Fixed
- **Setup Render Error**: Fixed `module 'bpy' has no attribute 'mathutils'` error
  - Changed `bpy.mathutils.Vector` to `mathutils.Vector` with proper import
  - Fixed vector operations for camera positioning and bounding box calculations

- **CFD Domain Parameters**: CFD domain now uses channel object parameters
  - Automatically detects existing channel for the same axis curve
  - Uses stored parameters from channel object instead of scene settings
  - Falls back to scene settings if no channel exists
  - Reports which parameter source is being used

- **CFD Domain Selection**: Fixed potential context error with `bpy.ops.object.select_all`
  - Replaced operator call with direct API for object selection (same fix as Build Channel)

---

## [0.2.1] - 2026-01-03

### Fixed
- **Build Channel Error**: Fixed `bpy.ops.object.select_all.poll() failed` error
  - Replaced operator call with direct API for object selection
  - No longer depends on context for select_all operation

---

## [0.2.0] - 2026-01-03

### Added
- **Edición Paramétrica Post-Creación**: Los canales ahora se pueden editar después de creados
  - Nuevo operador `CADHY_OT_UpdateChannel` para regenerar canales existentes
  - Panel Main detecta automáticamente si estás editando un canal existente
  - Los parámetros se leen directamente del objeto seleccionado
  - Botón "Update Channel" para regenerar con nuevos parámetros

- **Auto-Updater Funcional**: Sistema de actualizaciones desde GitHub
  - Verificación de nuevas versiones desde releases de GitHub
  - Descarga automática del ZIP de la última versión
  - Instalación con un clic (requiere reiniciar Blender)
  - Panel de Updates completamente funcional

### Fixed
- **Topología de Canales Abiertos**: Corregido el bug crítico de generación de mesh
  - Los canales TRAP/RECT ahora son abiertos (sin "techo")
  - Solo se generan 3 caras por segmento: piso, pared izquierda, pared derecha
  - Los canales circulares mantienen topología cerrada (tubería)

- **Lining Thickness**: Implementación correcta del espesor de revestimiento
  - Generación de perfiles interno y externo
  - Conexión correcta de superficies internas (agua) y externas (terreno)
  - Tapas en inicio y fin del canal
  - Top caps conectando inner y outer en los bordes superiores

### Improved
- **Resolución Adaptativa en Curvas**: Mayor densidad de mesh donde hay más curvatura
  - Algoritmo que detecta curvatura y ajusta el muestreo
  - Factor de refinamiento hasta 3x en curvas cerradas
  - Mejor calidad de mesh sin aumentar resolución global

- **Panel Main Mejorado**:
  - Modo Creación vs Modo Edición automático
  - Muestra información del canal seleccionado (nombre, eje, longitud)
  - Los parámetros son editables directamente desde el objeto

### Technical
- Nuevo archivo `op_update_channel.py` con operador de actualización
- Función `update_mesh_geometry()` para actualizar meshes existentes
- Función `generate_section_vertices_with_lining()` para perfiles con lining
- Función `_sample_curve_adaptive()` para muestreo adaptativo
- Integración completa del módulo `updater/` con el panel de Updates

---

## [0.1.1] - 2026-01-03

### Fixed
- **build_channel.py**: Removed unused variable assignment that could cause confusion
- **pt_sections.py**: Improved error handling with specific exception types instead of generic catch-all

### Improved
- **Main Panel**:
  - Added channel existence indicator with checkmark icon
  - Button now shows "Update Channel" when channel already exists
  - Added resolution warning for long curves (>100m) with low resolution (<0.5m)
  - Better visual feedback with calculated values display

- **CFD Panel**:
  - Added CFD domain status indicator showing if domain exists
  - Button changes to "Update CFD Domain" when domain already exists
  - Added water level validation warning when level exceeds channel height
  - Warning when water level is near maximum (>95% of height)
  - Validate button disabled when no mesh available

- **Sections Panel**:
  - Export buttons (CSV/JSON) now disabled when no sections exist
  - Added informative message "Generate sections first" when empty
  - Better curve length display with proper icon
  - Specific error messages for different failure cases

### Technical
- All panels now import `bpy` for object existence checks
- Consistent use of icons across all panels (CHECKMARK, ERROR, INFO)
- Better UX with contextual button labels

---

## [0.1.0] - 2026-01-03

### Added
- **Canal Paramétrico**: Generación de canales desde curvas de eje
  - Sección trapezoidal con ancho solera, talud, altura y freeboard
  - Sección rectangular
  - Sección circular
- **Dominio CFD**: Generación de volumen de fluido watertight
  - Extensiones inlet/outlet configurables
  - Modo de llenado: nivel de agua o completo
  - Patches automáticos (inlet, outlet, walls, top)
- **Secciones Transversales**: Generación de cortes a intervalos
  - Cálculos hidráulicos (área, perímetro mojado, radio hidráulico)
  - Exportación a CSV y JSON
- **Validación de Malla**: Verificación para CFD
  - Detección de mallas no-watertight
  - Detección de bordes non-manifold
  - Detección de auto-intersecciones
- **Exportación**: Formatos STL, OBJ, PLY
  - Limpieza automática para CFD
  - Reportes de proyecto en JSON/TXT
- **Materiales**: Presets para visualización
  - Concreto, agua, tierra, acero
- **Setup de Render**: Configuración automática de cámara y luces
- **Auto-Updater**: Verificación de actualizaciones desde GitHub
- **Integración BlenderGIS**: Soporte para import SHP/DEM (opcional)

### Technical
- Arquitectura modular: separación core/blender
- Scripts de desarrollo para Windows/macOS/Linux
- CI/CD con GitHub Actions
- Documentación completa

---

## Roadmap

### [0.3.0] - Planned
- Transiciones de sección (A→B)
- Bermas y cunetas compuestas
- Obras: alcantarilla simple, disipador básico

### [0.4.0] - Planned
- Integración completa BlenderGIS
- Terreno y alineamiento georeferenciado
- Soporte CRS/EPSG

### [0.4.0] - Planned
- Export orientado a OpenFOAM
- Patches CFD más robustos
- Lectura básica de resultados CFD
