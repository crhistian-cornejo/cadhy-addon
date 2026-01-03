# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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

### [0.2.0] - Planned
- Transiciones de sección (A→B)
- Bermas y cunetas compuestas
- Obras: alcantarilla simple, disipador básico

### [0.3.0] - Planned
- Integración completa BlenderGIS
- Terreno y alineamiento georeferenciado
- Soporte CRS/EPSG

### [0.4.0] - Planned
- Export orientado a OpenFOAM
- Patches CFD más robustos
- Lectura básica de resultados CFD
