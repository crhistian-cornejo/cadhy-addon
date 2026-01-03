<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# ESTA VACIO.. ESCRIBELO ACA NUEVAEEMNE COMPLETO EN BASE A LO QEU TE DI... PARA PODER DEACARGALO

Aquí está el PRD completo reescrito y también generado como archivo descargable:[^1][^2][^3]

Y por si tu cliente no muestra adjuntos, lo pego **completo** aquí en un solo bloque Markdown (idéntico al archivo):

```md
# PRD — CADHY (Blender Add-on)

Producto: **CADHY** (cadhy.app)  
Formato: Blender Add-on (Python)  
Versión objetivo (recomendación): **Blender 4.1 LTS+** (mínimo)  

CADHY es un toolkit vertical para **modelado paramétrico de infraestructura hidráulica** dentro de Blender, orientado a 3 salidas: **(1) render/visualización**, **(2) geometría limpia para CFD**, y **(3) extracción de cortes/perfiles y reportes**.

> Decisión explícita: el add-on debe generar **(A)** un “sólido”/malla de la obra (canal, revestimiento, estructuras) y **(B)** un “sólido”/malla del **dominio CFD** (volumen de fluido) listo para export y mallado.

---

## 1) Problema
- Construir una app CAD/topología robusta “tipo kernel” desde cero es extremadamente complejo.
- El objetivo real de CADHY no es BIM/CAD mecánico, sino **modelar canales/obras y preparar dominios CFD**.
- Blender ya incluye modelado, materiales, render y una API Python completa para crear paneles, operadores y generación de geometría vía scripts y nodos. (El add-on se apoya en eso). [web:29]

---

## 2) Objetivos

### Objetivo principal
Permitir que un usuario (sin saber Blender) pueda:
1) seleccionar o importar un **eje** (curva),
2) parametrizar una **sección hidráulica**,
3) generar automáticamente:
   - la **malla de la obra** (canal/revestimiento), y/o
   - la **malla del dominio CFD** (volumen de fluido watertight),
4) generar **cortes** por estación y exportar geometría para CFD.

### Objetivos secundarios
- Import geoespacial (SHP/DEM) como integración opcional (vía BlenderGIS). [web:50]
- Reportes (CSV/JSON) para consumir luego en tu app/UI CADHY.
- Auto-update desde GitHub Releases (fase 1) usando un updater embebido. [web:23]

### No-objetivos (por ahora)
- Reemplazar Revit/BIM (familias, IFC authoring completo, schedules).
- Garantizar B-Rep CAD con tolerancias y operaciones booleanas CAD-grade.

---

## 3) Usuarios y casos de uso

### Usuarios
- Ingeniero hidráulico: necesita modelar rápido y sacar cortes.
- CFD engineer: necesita dominio watertight y exportable.
- Visualizador: necesita render “bonito” y animaciones.

### Casos de uso MVP
- Crear un canal trapezoidal siguiendo una curva.
- Crear dominio CFD del canal con extensiones inlet/outlet.
- Generar cortes cada X metros y exportarlos.
- Exportar malla a STL/OBJ/PLY.

---

## 4) Definiciones
- **Eje**: curva de Blender (Bezier o polyline) que define el alineamiento.
- **Sección**: parámetros (ancho solera, talud, altura, radios, freeboard, etc.).
- **Malla obra**: geometría del canal/estructura (visualización + referencia).
- **Malla dominio CFD**: volumen de fluido cerrado (watertight) para mallado CFD.
- **Estación/chainage**: distancia acumulada sobre el eje.

---

## 5) Alcance funcional

### 5.1 Generación paramétrica por eje (Core)
**Inputs**
- Objeto curva (eje).
- Tipo de sección: trapezoidal / rectangular / circular.
- Parámetros: ancho, talud, altura, freeboard, radios, espesor de lining.
- Resolución: muestreo a lo largo del eje (paso en metros o nº de samples).

**Outputs**
- `CADHY_Channel` (malla obra).
- `CADHY_CFD_Domain` (malla dominio, opcional).
- Propiedades guardadas (para regenerar).

**Requisitos**
- “Build/Update” regenerativo (no duplicar objetos cada vez).
- Naming y colecciones consistentes.

### 5.2 Malla de obra (canal/estructura)
- Generar canal como malla:
  - Interior (superficie hidráulica) y opcionalmente espesor (lining).
- Elementos fase 2:
  - transiciones de sección (A→B),
  - bermas y cunetas compuestas,
  - obras: alcantarilla simple, disipador básico, canal con losa.

### 5.3 Malla de dominio CFD (fluido)
- Dominio cerrado (watertight) basado en:
  - la sección hidráulica,
  - nivel de agua (si es canal abierto), o
  - “fill full” (si se decide presurizado más adelante).
- Extensiones inlet/outlet para desarrollo de flujo.
- Cierre por tapas (caps) automático.
- Asignación de “patches” para CFD:
  - `inlet`, `outlet`, `walls`, `top` (si aplica).
  - Implementación: material slots o vertex groups.

### 5.4 Cortes y perfiles
- Generación automática de estaciones:
  - start, end, step (m).
- Salidas:
  - curvas de perfil y/o mesh slice en colección `CADHY_Sections`.
  - export `sections.csv` con (station, coords) + métricas.

### 5.5 Medidas y reportes
- Longitud de eje.
- Área hidráulica teórica por sección (según tipo).
- Perímetro mojado teórico (si aplica).
- Volumen de dominio CFD (si watertight).
- Export `report.json` para CADHY UI futura.

### 5.6 Materiales, texturas y render
- Materiales base:
  - concreto, tierra, acero (estructuras), agua (visual).
- Botón “Setup Render”:
  - crea cámara, luces, HDRI opcional.
- Nota: Blender ya gestiona materiales/render; el add-on solo automatiza. [web:29]

### 5.7 Import geoespacial (opcional)
- Integración con BlenderGIS:
  - import SHP (eje),
  - import DEM/GeoTIFF (terreno).
- BlenderGIS declara soporte de import de formatos GIS comunes (Shapefile, geotiff DEM, etc.). [web:50]

### 5.8 Export para CFD
- Export estándar: STL/OBJ/PLY.
- Preset “CFD Clean”:
  - triangulación,
  - merge by distance,
  - normales coherentes,
  - detectar non-manifold y advertir.

---

## 6) Requisitos no funcionales

### Compatibilidad
- Blender 4.1 LTS+ recomendado como mínimo (definir en `bl_info`). [web:29]
- Windows/macOS/Linux.

### Distribución
- Python-only (evitar binarios nativos en v1).
- ZIP instalable desde Blender Preferences.

### Rendimiento
- Ejes largos (km) con densidad configurable.
- Controles de resolución y preview rápido (LOD).

### Robustez
- Prioridad máxima: dominio CFD watertight.
- Mensajes claros (warnings) cuando hay self-intersections o geometría inválida.

---

## 7) UX — diseñado para “no sé Blender”

### Principio de producto
**Un panel, flujo guiado**:
1) Input (eje) → 2) Sección → 3) Build → 4) CFD → 5) Sections → 6) Export

### Ubicación
- Sidebar del 3D View (N-panel) → pestaña **CADHY**.

### Paneles
- `CADHY > Main`
  - Selector de curva eje (o usar objeto activo).
  - Sección: tipo + parámetros.
  - Botón: Build/Update Channel.
- `CADHY > CFD`
  - Toggle: Generate CFD Domain.
  - Inlet/outlet extensions.
  - Water level / fill mode.
  - Botón: Build CFD Domain.
  - Botón: Validate Mesh.
- `CADHY > Sections`
  - Step (m), rango.
  - Botón: Generate Sections.
  - Export CSV.
- `CADHY > Export`
  - Export mesh + report.
- `CADHY > Render`
  - Assign materials.
  - Setup render.
- `CADHY > Updates`
  - Check updates.

---

## 8) Arquitectura del add-on (estilo “addons grandes”)

Blender add-ons se estructuran con `bl_info`, y funciones `register()` / `unregister()` para registrar clases (Panels/Operators/PropertyGroups). [web:29]

### 8.1 Principios
- Separar “core” (lógica geométrica y datos) de “blender layer” (UI, operators, bpy).
- Evitar `bpy.ops` cuando se pueda; preferir APIs de datos (más reproducible).
- Parametrización guardada como propiedades en Scene/Object.

### 8.2 Estructura de carpetas sugerida
```

cadhy/
__init__.py
bl_info.py
register.py

core/
model/
channel_params.py
cfd_params.py
sections_params.py
geom/
build_channel.py
build_cfd_domain.py
build_sections.py
mesh_validate.py
mesh_cleanup.py
io/
export_mesh.py
export_reports.py
util/
units.py
naming.py
logging.py
versioning.py

blender/
properties/
scene_props.py
object_props.py
operators/
op_build_channel.py
op_build_cfd_domain.py
op_generate_sections.py
op_export_cfd.py
op_export_report.py
op_dev_reload.py
panels/
pt_main.py
pt_cfd.py
pt_sections.py
pt_export.py
pt_render.py
pt_updates.py

integrations/
blendergis_adapter.py

updater/
addon_updater.py
addon_updater_ops.py

assets/
materials.blend

tests/
smoke_create_channel.py

```

### 8.3 Registro (register/unregister)
- `__init__.py` expone `register()` y `unregister()`.
- `register.py` mantiene una tupla `classes = (...)` y registra/desregistra en orden.
- Propiedades:
  - `Scene` para defaults globales.
  - `Object` para settings del canal/dominio.

---

## 9) Modelo de datos (properties)

### 9.1 `CADHYSceneSettings` (Scene)
- units: m (default).
- default_resolution_m.
- georef: CRS string (EPSG), offset vector (x0,y0,z0).

### 9.2 `CADHYChannelSettings` (Object: canal)
- section_type: TRAP/RECT/CIRC.
- bottom_width, side_slope, height, freeboard.
- lining_thickness.
- resolution_m.

### 9.3 `CADHYCFDSettings` (Object: dominio)
- enabled.
- inlet_extension_m, outlet_extension_m.
- water_level_m / fill_mode.
- cap_inlet_outlet.
- patch_tags (strings o enums).

---

## 10) Flujo de desarrollo (VS Code + Blender)

### Objetivo
No reinstalar ZIP a cada cambio.

### Workflow recomendado
- Instalar el add-on como carpeta (o symlink) en `scripts/addons`.
- Editar en VS Code.
- En Blender: usar “Reload Scripts” y/o un operador `CADHY_OT_dev_reload` que haga `importlib.reload`.

---

## 11) Distribución y Auto-update

### Recomendación para CADHY (fase 1)
Updater embebido + GitHub Releases.

`blender-addon-updater` (CGCookie) permite check de updates y “one-click install” desde Blender, descargando desde GitHub tags o releases. [web:23]

### Pipeline
- GitHub Actions:
  - build zip
  - publicar Release con tag semver `vX.Y.Z`
- Add-on:
  - Panel “Updates” para check e instalación.

---

## 12) Roadmap

### Fase 0 (1–3 días)
- Add-on instalable.
- Panel Main.
- Build canal simple por curva.

### Fase 1 (1–2 semanas) — MVP
- Canal paramétrico + dominio CFD watertight.
- Cortes por estación.
- Export malla + report.
- Updater + releases.

### Fase 2 (2–4 semanas)
- Integración BlenderGIS (SHP/DEM) opcional.
- Terreno y alineamiento georef.

### Fase 3 (4–8 semanas)
- Patches CFD más robustos.
- Export orientado a OpenFOAM workflow.
- Lectura básica de resultados (para CADHY UI futura).

---

## 13) Criterios de aceptación (MVP)
1. Con una curva seleccionada, generar **malla de canal** y **malla dominio CFD** en un clic.
2. Cambiar parámetros y regenerar sin duplicar objetos.
3. Dominio CFD exportable (watertight) con validación/warnings.
4. Cortes cada X metros visibles y exportables.
5. ZIP instalable y funcional en Windows/macOS/Linux (Python-only).

---

## 14) Riesgos y mitigaciones
- Self-intersections en curvas cerradas o radios pequeños.
  - Mitigación: límites de resolución, smoothing y validación.
- Coordenadas UTM grandes (precisión float).
  - Mitigación: offset local + metadata.
- Cambios de API entre versiones Blender.
  - Mitigación: soportar mínimo 4.1 LTS y testear en 2–3 versiones.
```

Si me dices tu sistema (Windows/macOS/Linux) y si usarás Blender 4.1 LTS o 4.2+, te armo el **scaffold de repo** (árbol + `__init__.py` + `register.py` + primer Panel/Operator) listo para copiar/pegar.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

[^2]: https://github.com/CGCookie/blender-addon-updater/blob/master/README.md

[^3]: https://github.com/domlysz/BlenderGIS

[^4]: https://docs.blender.org/api/blender_python_api_2_65_9/info_tutorial_addon.html

[^5]: https://www.youtube.com/watch?v=Uoo4dpUlDJE

[^6]: http://www.s-t.com/local/add-a-properties-panel-to

[^7]: https://blenderartists.org/t/blender-addon-development/1160488

[^8]: https://github.com/ptabriz/Geospatial_studio_blender

[^9]: https://community.osarch.org/discussion/759/blender-create-your-first-blender-add-on

[^10]: https://github.com/CGCookie/blender-addon-updater

[^11]: https://github.com/domlysz/BlenderGIS/wiki/Import-DEM-grid

[^12]: https://www.youtube.com/watch?v=Ywza-zyAJzE

[^13]: https://github.com/CGCookie/blender-addon-updater/releases

[^14]: https://www.reddit.com/r/blenderhelp/comments/zcfqr6/custom_addon_not_registering/

[^15]: https://github.com/CGCookie/blender-addon-updater/tags

[^16]: https://www.youtube.com/watch?v=WviTi0q2BpA

[^17]: https://www.reddit.com/r/blenderhelp/comments/qhsd4j/no_attribute_register_error_of_blender/

[^18]: https://github.com/CGCookie/blender-addon-updater/issues

[^19]: https://github.com/domlysz/BlenderGIS/wiki/Shapefile-import

[^20]: https://www.reddit.com/r/blenderpython/comments/o6njvi/addons_overriding_each_other_need_someone_to_hold/

