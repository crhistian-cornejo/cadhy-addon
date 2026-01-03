# CADHY - Blender Add-on

**Parametric modeling toolkit for hydraulic infrastructure and CFD domain generation**

![Blender](https://img.shields.io/badge/Blender-4.1+-orange)
![License](https://img.shields.io/badge/License-MIT-blue)
![Version](https://img.shields.io/badge/Version-0.1.0-green)

## Overview

CADHY is a Blender add-on designed for hydraulic engineers, CFD specialists, and visualization professionals. It enables parametric modeling of hydraulic channels and structures, with automatic generation of CFD-ready fluid domains.

### Key Features

- **Parametric Channel Generation**: Create trapezoidal, rectangular, or circular channels from curve axes
- **CFD Domain Generation**: Automatic watertight fluid domain with inlet/outlet extensions
- **Cross-Section Analysis**: Generate sections at specified intervals with hydraulic calculations
- **Mesh Validation**: Check geometry for CFD compatibility (manifold, watertight)
- **Export Ready**: STL/OBJ/PLY export with CFD cleanup options
- **BlenderGIS Integration**: Import SHP/DEM for georeferenced projects (optional)

## Installation

### Requirements
- Blender 4.1 LTS or higher
- Windows / macOS / Linux

### Install from ZIP
1. Download the latest release ZIP from [Releases](https://github.com/cadhy/cadhy-addon/releases)
2. In Blender: `Edit > Preferences > Add-ons > Install...`
3. Select the downloaded ZIP file
4. Enable "CADHY" in the add-ons list

### Development Installation
```bash
# Clone or symlink to Blender's addons folder
cd ~/.config/blender/4.1/scripts/addons/  # Linux
cd ~/Library/Application Support/Blender/4.1/scripts/addons/  # macOS
cd %APPDATA%\Blender Foundation\Blender\4.1\scripts\addons\  # Windows

# Symlink the addon
ln -s /path/to/CADHY-addon/cadhy cadhy
```

## Quick Start

1. **Create an Axis**: Add a Bezier curve in Blender (`Shift+A > Curve > Bezier`)
2. **Open CADHY Panel**: Press `N` in 3D View, select "CADHY" tab
3. **Select Axis**: Choose your curve in the "Axis" field
4. **Configure Section**: Set section type and parameters
5. **Build**: Click "Build Channel" to generate geometry

## Panel Overview

### CADHY - Main
- Axis selection
- Section type (Trapezoidal/Rectangular/Circular)
- Section parameters (width, slope, height, freeboard)
- Build Channel button

### CADHY - CFD Domain
- Enable/disable CFD generation
- Fill mode (water level or full)
- Inlet/outlet extensions
- Mesh validation status

### CADHY - Sections
- Station range configuration
- Section step interval
- Generate and export sections

### CADHY - Export
- Mesh export (STL/OBJ/PLY)
- Report export (JSON/CSV/TXT)
- Quick export all

### CADHY - Render
- Material presets (Concrete, Water, Earth, Steel)
- Render scene setup
- Viewport shading controls

### CADHY - Updates
- Version information
- Update checker
- Development tools

## Project Structure

```
cadhy/
├── __init__.py           # Main entry point with bl_info
├── register.py           # Class registration
├── core/                 # Core logic (Blender-independent)
│   ├── model/           # Data structures
│   │   ├── channel_params.py
│   │   ├── cfd_params.py
│   │   └── sections_params.py
│   ├── geom/            # Geometry generation
│   │   ├── build_channel.py
│   │   ├── build_cfd_domain.py
│   │   ├── build_sections.py
│   │   ├── mesh_validate.py
│   │   └── mesh_cleanup.py
│   ├── io/              # Import/Export
│   │   ├── export_mesh.py
│   │   └── export_reports.py
│   └── util/            # Utilities
│       ├── units.py
│       ├── naming.py
│       ├── logging.py
│       └── versioning.py
├── blender/             # Blender-specific code
│   ├── properties/      # PropertyGroups
│   ├── operators/       # Operators
│   └── panels/          # UI Panels
├── integrations/        # Third-party integrations
│   └── blendergis_adapter.py
├── updater/             # Auto-update system
├── assets/              # Asset files
└── tests/               # Test scripts
```

## API Reference

### Operators

| Operator | Description |
|----------|-------------|
| `cadhy.build_channel` | Generate channel mesh from axis |
| `cadhy.build_cfd_domain` | Generate CFD fluid domain |
| `cadhy.generate_sections` | Create cross-sections |
| `cadhy.validate_mesh` | Validate mesh for CFD |
| `cadhy.export_cfd` | Export mesh for CFD |
| `cadhy.export_report` | Export project report |
| `cadhy.setup_render` | Setup render environment |
| `cadhy.assign_materials` | Apply material presets |

### Properties

Access via `bpy.context.scene.cadhy`:
- `axis_object` - Selected curve axis
- `section_type` - TRAP/RECT/CIRC
- `bottom_width`, `side_slope`, `height`, `freeboard`
- `cfd_enabled`, `cfd_water_level`, `cfd_inlet_extension`, `cfd_outlet_extension`

## Development

### Reload During Development
Use the "Reload CADHY" button in the Updates panel, or:
```python
import importlib
import cadhy
importlib.reload(cadhy)
```

### Run Smoke Tests
```python
exec(open('/path/to/cadhy/tests/smoke_create_channel.py').read())
```

## Roadmap

- [x] **Phase 0**: Basic channel generation
- [ ] **Phase 1**: CFD domain + sections + export
- [ ] **Phase 2**: BlenderGIS integration
- [ ] **Phase 3**: OpenFOAM workflow integration

## License

MIT License - See LICENSE file

## Links

- Website: [cadhy.app](https://cadhy.app)
- Documentation: [cadhy.app/docs](https://cadhy.app/docs)
- Issues: [GitHub Issues](https://github.com/cadhy/cadhy-addon/issues)
