# CADHY - Blender Add-on

<p align="center">
  <img src="https://img.shields.io/badge/Blender-4.1+-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue" alt="License">
  <img src="https://img.shields.io/github/v/release/crhistian-cornejo/cadhy-addon" alt="Release">
  <img src="https://img.shields.io/github/actions/workflow/status/crhistian-cornejo/cadhy-addon/ci.yml?branch=main" alt="CI">
</p>

**Toolkit paramétrico para modelado de infraestructura hidráulica y generación de dominios CFD en Blender.**

CADHY permite a ingenieros hidráulicos, especialistas CFD y profesionales de visualización crear canales paramétricos y dominios de fluido listos para simulación, todo desde una interfaz simple en Blender.

---

## 🎯 ¿Qué hace CADHY?

1. **Genera canales paramétricos** a partir de una curva (eje de alineamiento)
2. **Crea dominios CFD watertight** (volumen de fluido cerrado) para simulación
3. **Genera cortes transversales** con cálculos hidráulicos automáticos
4. **Exporta geometría** en formatos STL/OBJ/PLY listos para mallado CFD
5. **Produce reportes** en JSON/CSV para integración con otras herramientas

---

## 📦 Instalación

### Opción 1: Desde Release (Recomendado)

1. Descarga `cadhy-X.Y.Z.zip` desde [Releases](https://github.com/crhistian-cornejo/cadhy-addon/releases)
2. En Blender: `Edit > Preferences > Add-ons > Install...`
3. Selecciona el archivo ZIP descargado
4. Activa "CADHY" en la lista de add-ons
5. El panel aparece en la barra lateral del 3D View (tecla `N`)

### Opción 2: Desarrollo (Symlink)

```bash
# Clonar repositorio
git clone https://github.com/crhistian-cornejo/cadhy-addon.git
cd cadhy-addon

# Crear symlink a Blender addons
python3 scripts/setup_dev.py

# En Windows (PowerShell como Admin)
.\scripts\setup_dev.ps1
```

### Requisitos
- **Blender 4.1 LTS** o superior
- Windows / macOS / Linux
- Sin dependencias externas (Python puro)

---

## 🚀 Uso Rápido

### 1. Crear un Eje (Curva)
```
Shift+A > Curve > Bezier
```
Modela la curva siguiendo el alineamiento de tu canal.

### 2. Abrir Panel CADHY
Presiona `N` en el 3D View y selecciona la pestaña **CADHY**.

### 3. Configurar y Generar

| Paso | Acción |
|------|--------|
| **Seleccionar Eje** | Elige tu curva en el campo "Axis" |
| **Tipo de Sección** | Trapezoidal / Rectangular / Circular |
| **Parámetros** | Ancho, talud, altura, freeboard |
| **Build Channel** | Genera la malla del canal |
| **Build CFD Domain** | Genera el dominio de fluido |

### 4. Exportar
- **Malla CFD**: `CADHY > Export > Export CFD Mesh`
- **Reporte**: `CADHY > Export > Export Report`

---

## 🔧 Paneles

### CADHY - Main
- Selección de eje (curva)
- Tipo de sección hidráulica
- Parámetros geométricos
- Botón Build Channel

### CADHY - CFD Domain
- Nivel de agua / modo de llenado
- Extensiones inlet/outlet
- Validación de malla
- Botón Build CFD Domain

### CADHY - Sections
- Rango de estaciones (inicio, fin, paso)
- Generación de cortes
- Exportación CSV/JSON

### CADHY - Export
- Exportación de mallas (STL/OBJ/PLY)
- Reportes de proyecto

### CADHY - Render
- Materiales predefinidos (concreto, agua, tierra)
- Setup de escena para render

### CADHY - Updates
- Verificar actualizaciones
- Información de versión

---

## 📐 Tipos de Sección

| Tipo | Parámetros | Uso |
|------|------------|-----|
| **Trapezoidal** | Ancho solera, talud (H:V), altura | Canales abiertos |
| **Rectangular** | Ancho, altura | Canales revestidos |
| **Circular** | Diámetro | Tuberías, alcantarillas |

---

## 🔬 Flujo CFD

```
Curva (Eje) → Canal Paramétrico → Dominio CFD → Validación → Export STL → Mallado (externo)
```

El dominio CFD incluye:
- **Extensión inlet**: Para desarrollo de flujo
- **Extensión outlet**: Para estabilización
- **Patches**: inlet, outlet, walls, top (superficie libre)
- **Validación**: Watertight, manifold, sin auto-intersecciones

---

## 📁 Estructura del Proyecto

```
cadhy-addon/
├── cadhy/                    # Código del addon
│   ├── __init__.py          # Entry point
│   ├── register.py          # Registro de clases
│   ├── core/                # Lógica (independiente de Blender)
│   │   ├── model/           # Estructuras de datos
│   │   ├── geom/            # Generación de geometría
│   │   ├── io/              # Import/Export
│   │   └── util/            # Utilidades
│   ├── blender/             # Código específico Blender
│   │   ├── properties/      # PropertyGroups
│   │   ├── operators/       # Operadores
│   │   └── panels/          # Paneles UI
│   ├── integrations/        # BlenderGIS, etc.
│   └── updater/             # Auto-actualización
├── scripts/                  # Scripts de desarrollo
│   ├── build.py             # Generar ZIP
│   ├── setup_dev.py         # Setup desarrollo
│   ├── setup_dev.bat        # Windows CMD
│   └── setup_dev.ps1        # Windows PowerShell
├── .github/workflows/        # CI/CD
├── pyproject.toml           # Configuración proyecto
└── README.md
```

---

## 🛠️ Desarrollo

### Generar ZIP Instalable
```bash
python3 scripts/build.py
# Output: dist/cadhy-X.Y.Z.zip
```

### Setup Desarrollo
```bash
# macOS/Linux
python3 scripts/setup_dev.py

# Windows (PowerShell como Admin)
.\scripts\setup_dev.ps1 -Force
```

### Crear Release
```bash
# 1. Actualizar versión en cadhy/__init__.py
# 2. Commit y tag
git add -A && git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --tags
# GitHub Actions genera el release automáticamente
```

### Recargar en Desarrollo
En Blender: `CADHY > Updates > Reload Addon`

---

## 📄 Licencia

Este proyecto está bajo la licencia **GPL-3.0** - compatible con Blender y estándar para addons open source.

Ver [LICENSE](LICENSE) para más detalles.

---

## 🔗 Enlaces

- **Website**: [cadhy.app](https://cadhy.app)
- **Documentación**: [cadhy.app/docs](https://cadhy.app/docs)
- **Issues**: [GitHub Issues](https://github.com/crhistian-cornejo/cadhy-addon/issues)
- **Releases**: [GitHub Releases](https://github.com/crhistian-cornejo/cadhy-addon/releases)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías.

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Add nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
