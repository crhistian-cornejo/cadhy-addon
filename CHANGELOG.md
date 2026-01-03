# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
