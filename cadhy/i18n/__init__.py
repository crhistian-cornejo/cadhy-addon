"""
CADHY Internationalization Module
Provides translation support for the addon UI.

Usage:
    from cadhy.i18n import translate as T

    # In operator/panel:
    label = T("Build Channel")
"""

import bpy

# Translation dictionary format:
# "context": {
#     "msgid": {
#         "lang_code": "translation"
#     }
# }
#
# Blender uses contexts to disambiguate identical strings with different meanings.
# Common contexts: "*" (default), "Operator", "Panel"

TRANSLATIONS = {
    "es_ES": {
        # Operators
        ("*", "Build Channel"): "Construir Canal",
        ("*", "Update Channel"): "Actualizar Canal",
        ("*", "Build CFD Domain"): "Construir Dominio CFD",
        ("*", "Generate Sections"): "Generar Secciones",
        ("*", "Export CFD"): "Exportar CFD",
        ("*", "Validate Mesh"): "Validar Malla",
        ("*", "Setup Render"): "Configurar Render",
        ("*", "Assign Materials"): "Asignar Materiales",
        ("*", "Export Report"): "Exportar Reporte",
        ("*", "Refresh Info"): "Actualizar Info",
        # Panels
        ("*", "CADHY - Main"): "CADHY - Principal",
        ("*", "Channel Info"): "Info del Canal",
        ("*", "CFD Domain"): "Dominio CFD",
        ("*", "Sections"): "Secciones",
        ("*", "Export"): "Exportar",
        ("*", "Render"): "Render",
        ("*", "Updates"): "Actualizaciones",
        # Section types
        ("*", "Trapezoidal"): "Trapezoidal",
        ("*", "Rectangular"): "Rectangular",
        ("*", "Circular"): "Circular",
        # Parameters
        ("*", "Bottom Width"): "Ancho de Solera",
        ("*", "Side Slope"): "Talud Lateral",
        ("*", "Height"): "Altura",
        ("*", "Freeboard"): "Bordo Libre",
        ("*", "Lining Thickness"): "Espesor de Revestimiento",
        ("*", "Resolution"): "Resolución",
        ("*", "Profile Resolution"): "Resolución del Perfil",
        ("*", "Subdivide Profile"): "Subdividir Perfil",
        ("*", "Section Type"): "Tipo de Sección",
        ("*", "Section Parameters"): "Parámetros de Sección",
        ("*", "Axis (Alignment)"): "Eje (Alineamiento)",
        # Info panel
        ("*", "Geometry"): "Geometría",
        ("*", "Profile & Slope"): "Perfil y Pendiente",
        ("*", "Hydraulics"): "Hidráulica",
        ("*", "Mesh Stats"): "Estadísticas de Malla",
        ("*", "Length"): "Longitud",
        ("*", "Slope"): "Pendiente",
        ("*", "Water Depth"): "Tirante de Agua",
        ("*", "Area"): "Área",
        ("*", "Wetted Perimeter"): "Perímetro Mojado",
        ("*", "Hydraulic Radius"): "Radio Hidráulico",
        ("*", "Velocity"): "Velocidad",
        ("*", "Discharge"): "Caudal",
        ("*", "Vertices"): "Vértices",
        ("*", "Edges"): "Aristas",
        ("*", "Faces"): "Caras",
        ("*", "Triangles"): "Triángulos",
        ("*", "Volume"): "Volumen",
        ("*", "Surface Area"): "Área Superficial",
        ("*", "Manifold"): "Manifold",
        ("*", "Watertight"): "Estanco",
        ("*", "Not Watertight"): "No Estanco",
        # CFD
        ("*", "Water Level"): "Nivel de Agua",
        ("*", "Inlet Extension"): "Extensión de Entrada",
        ("*", "Outlet Extension"): "Extensión de Salida",
        ("*", "Fill Mode"): "Modo de Llenado",
        ("*", "Full"): "Completo",
        # Messages
        ("*", "Channel created successfully"): "Canal creado exitosamente",
        ("*", "No valid curve selected as axis"): "No hay curva válida seleccionada como eje",
        ("*", "Failed to generate channel geometry"): "Error al generar geometría del canal",
        ("*", "Source axis curve not found"): "Curva de eje fuente no encontrada",
        ("*", "Click Refresh to calculate"): "Click en Actualizar para calcular",
        # Preferences
        ("*", "Log Level"): "Nivel de Log",
        ("*", "Developer Mode"): "Modo Desarrollador",
        ("*", "Enable logging to file"): "Habilitar log a archivo",
        ("*", "CFD Solver Path"): "Ruta del Solver CFD",
    },
    "pt_BR": {
        # Operators
        ("*", "Build Channel"): "Construir Canal",
        ("*", "Update Channel"): "Atualizar Canal",
        ("*", "Build CFD Domain"): "Construir Domínio CFD",
        ("*", "Generate Sections"): "Gerar Seções",
        # Parameters
        ("*", "Bottom Width"): "Largura do Fundo",
        ("*", "Side Slope"): "Talude Lateral",
        ("*", "Height"): "Altura",
        ("*", "Freeboard"): "Borda Livre",
        ("*", "Lining Thickness"): "Espessura do Revestimento",
        ("*", "Resolution"): "Resolução",
        # Section types
        ("*", "Trapezoidal"): "Trapezoidal",
        ("*", "Rectangular"): "Retangular",
        ("*", "Circular"): "Circular",
    },
    "fr_FR": {
        # Operators
        ("*", "Build Channel"): "Construire Canal",
        ("*", "Update Channel"): "Mettre à jour Canal",
        ("*", "Build CFD Domain"): "Construire Domaine CFD",
        # Parameters
        ("*", "Bottom Width"): "Largeur du Fond",
        ("*", "Side Slope"): "Pente Latérale",
        ("*", "Height"): "Hauteur",
        ("*", "Freeboard"): "Revanche",
        ("*", "Lining Thickness"): "Épaisseur du Revêtement",
    },
}


def _build_translation_dict():
    """Convert TRANSLATIONS to Blender's expected format."""
    translations_dict = {}

    for lang, strings in TRANSLATIONS.items():
        if lang not in translations_dict:
            translations_dict[lang] = {}
        for (context, msgid), msgstr in strings.items():
            translations_dict[lang][(context, msgid)] = msgstr

    return translations_dict


def translate(text: str, context: str = "*") -> str:
    """
    Get translated text for current Blender language.

    Args:
        text: Original English text
        context: Translation context (default "*")

    Returns:
        Translated text or original if no translation found
    """
    try:
        # Get current Blender language
        lang = bpy.app.translations.locale

        # Check if we have translations for this language
        if lang in TRANSLATIONS:
            key = (context, text)
            if key in TRANSLATIONS[lang]:
                return TRANSLATIONS[lang][key]

        # Try base language (e.g., "es" from "es_ES")
        base_lang = lang.split("_")[0]
        for full_lang in TRANSLATIONS:
            if full_lang.startswith(base_lang + "_"):
                key = (context, text)
                if key in TRANSLATIONS[full_lang]:
                    return TRANSLATIONS[full_lang][key]

    except Exception:
        pass

    # Return original text if no translation
    return text


# Shorthand alias
T = translate


def register():
    """Register translations with Blender."""
    try:
        translations_dict = _build_translation_dict()
        bpy.app.translations.register(__name__, translations_dict)
    except Exception:
        # Translations not critical, fail silently
        pass


def unregister():
    """Unregister translations from Blender."""
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
