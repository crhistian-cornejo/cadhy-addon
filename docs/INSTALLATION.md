# Guía de Instalación - CADHY

## Requisitos del Sistema

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| Blender | 4.1 LTS | 4.2+ |
| Sistema Operativo | Windows 10, macOS 10.15, Ubuntu 20.04 | Últimas versiones |
| RAM | 4 GB | 8 GB+ |
| GPU | Cualquiera | GPU con soporte CUDA/Metal |

## Instalación desde Release

### Paso 1: Descargar

1. Ve a [Releases](https://github.com/crhistian-cornejo/cadhy-addon/releases)
2. Descarga `cadhy-X.Y.Z.zip` (última versión)
3. **NO descomprimas** el archivo ZIP

### Paso 2: Instalar en Blender

1. Abre Blender
2. Ve a `Edit > Preferences` (o `Ctrl+,`)
3. Selecciona la pestaña `Add-ons`
4. Click en `Install...` (esquina superior derecha)
5. Navega y selecciona el archivo `cadhy-X.Y.Z.zip`
6. Click en `Install Add-on`

### Paso 3: Activar

1. En la lista de add-ons, busca "CADHY"
2. Marca la casilla para activarlo
3. Click en `Save Preferences` (opcional, para que persista)

### Paso 4: Verificar

1. En el 3D View, presiona `N` para abrir la barra lateral
2. Deberías ver la pestaña "CADHY"

## Instalación para Desarrollo

### Windows

#### Opción A: PowerShell (Recomendado)

```powershell
# Clonar repositorio
git clone https://github.com/crhistian-cornejo/cadhy-addon.git
cd cadhy-addon

# Ejecutar setup (como Administrador o con Developer Mode)
.\scripts\setup_dev.ps1
```

#### Opción B: CMD

```cmd
git clone https://github.com/crhistian-cornejo/cadhy-addon.git
cd cadhy-addon
scripts\setup_dev.bat
```

#### Requisitos Windows

Para crear symlinks necesitas **una** de estas opciones:
1. Ejecutar como Administrador
2. Habilitar Developer Mode: `Settings > Update & Security > For developers`

### macOS / Linux

```bash
# Clonar repositorio
git clone https://github.com/crhistian-cornejo/cadhy-addon.git
cd cadhy-addon

# Ejecutar setup
python3 scripts/setup_dev.py
```

### Especificar Ruta de Blender

Si tienes múltiples versiones de Blender o una instalación no estándar:

```bash
# Ver rutas detectadas
python3 scripts/setup_dev.py --list-paths

# Especificar ruta manualmente
python3 scripts/setup_dev.py --blender-path "/path/to/blender/4.1/scripts/addons"
```

## Rutas de Addons por Sistema

### Windows
```
%APPDATA%\Blender Foundation\Blender\4.1\scripts\addons\
```

### macOS
```
~/Library/Application Support/Blender/4.1/scripts/addons/
```

### Linux
```
~/.config/blender/4.1/scripts/addons/
```

## Actualización

### Desde Blender

1. `CADHY > Updates > Check for Updates`
2. Si hay actualización disponible, sigue las instrucciones

### Manual

1. Desactiva el addon en Preferences
2. Click en `Remove`
3. Instala la nueva versión siguiendo los pasos anteriores

## Desinstalación

1. `Edit > Preferences > Add-ons`
2. Busca "CADHY"
3. Click en la flecha para expandir
4. Click en `Remove`

Para desarrollo:
```bash
python3 scripts/setup_dev.py --remove
```

## Solución de Problemas

### El addon no aparece después de instalar

- Verifica que instalaste el ZIP sin descomprimir
- Reinicia Blender
- Verifica la versión de Blender (mínimo 4.1)

### Error de permisos en Windows

- Ejecuta PowerShell como Administrador, o
- Habilita Developer Mode en Windows Settings

### El panel no aparece

- Presiona `N` en el 3D View
- Busca la pestaña "CADHY" en la barra lateral

### Errores al cargar

Verifica la consola de Blender:
- `Window > Toggle System Console` (Windows)
- Ejecuta Blender desde terminal (macOS/Linux)

## Soporte

- **Issues**: [GitHub Issues](https://github.com/crhistian-cornejo/cadhy-addon/issues)
- **Documentación**: [cadhy.app/docs](https://cadhy.app/docs)
