# Contribuir a CADHY

¡Gracias por tu interés en contribuir a CADHY! Este documento proporciona guías para contribuir al proyecto.

## Código de Conducta

Este proyecto sigue un código de conducta abierto y respetuoso. Por favor, sé amable y constructivo en todas las interacciones.

## Cómo Contribuir

### Reportar Bugs

1. Verifica que el bug no haya sido reportado en [Issues](https://github.com/crhistian-cornejo/cadhy-addon/issues)
2. Crea un nuevo issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Versión de Blender y CADHY
   - Sistema operativo

### Sugerir Funcionalidades

1. Abre un issue con la etiqueta `enhancement`
2. Describe la funcionalidad y su caso de uso
3. Explica por qué sería útil para otros usuarios

### Pull Requests

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-funcionalidad
   ```
3. **Desarrolla** siguiendo las guías de estilo
4. **Prueba** tus cambios en Blender
5. **Commit** con mensajes descriptivos:
   ```bash
   git commit -m "Add: nueva funcionalidad para X"
   ```
6. **Push** a tu fork:
   ```bash
   git push origin feature/mi-funcionalidad
   ```
7. **Abre un Pull Request** hacia `main`

## Configuración de Desarrollo

### Requisitos

- Python 3.10+
- Blender 4.1+
- Git

### Setup

```bash
# Clonar
git clone https://github.com/crhistian-cornejo/cadhy-addon.git
cd cadhy-addon

# Crear symlink a Blender
python3 scripts/setup_dev.py

# Instalar herramientas de desarrollo (opcional)
pip install ruff pytest
```

### Estructura del Código

```
cadhy/
├── core/           # Lógica pura Python (sin bpy)
│   ├── model/      # Dataclasses y parámetros
│   ├── geom/       # Generación de geometría
│   ├── io/         # Import/Export
│   └── util/       # Utilidades
├── blender/        # Código específico de Blender
│   ├── properties/ # PropertyGroups
│   ├── operators/  # Operadores
│   └── panels/     # UI Panels
└── ...
```

### Principios de Diseño

1. **Separar core de blender**: La lógica en `core/` no debe importar `bpy`
2. **Evitar `bpy.ops`**: Preferir APIs de datos cuando sea posible
3. **Naming consistente**: Usar prefijos `CADHY_` para objetos Blender
4. **Documentar**: Docstrings en funciones públicas

## Guía de Estilo

### Python

- **Formatter**: Ruff
- **Line length**: 120 caracteres
- **Imports**: Ordenados (stdlib, third-party, local)

```bash
# Verificar estilo
ruff check cadhy/
ruff format cadhy/
```

### Commits

Formato: `<tipo>: <descripción>`

Tipos:
- `Add`: Nueva funcionalidad
- `Fix`: Corrección de bug
- `Update`: Actualización de funcionalidad existente
- `Refactor`: Refactorización sin cambio de funcionalidad
- `Docs`: Documentación
- `CI`: Cambios en CI/CD

### Blender

- Usar `bl_idname` con formato `cadhy.<nombre>`
- Paneles en categoría "CADHY"
- Operadores con `bl_options = {'REGISTER', 'UNDO'}` cuando aplique

## Testing

### Smoke Test Manual

```python
# En Blender Python Console
exec(open('/path/to/cadhy/tests/smoke_create_channel.py').read())
```

### Verificar Sintaxis

```bash
python3 -c "import ast; ast.parse(open('cadhy/__init__.py').read())"
```

## Releases

Los releases se generan automáticamente via GitHub Actions cuando se crea un tag:

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

## Preguntas

Si tienes preguntas, abre un issue con la etiqueta `question`.

---

¡Gracias por contribuir! 🎉
