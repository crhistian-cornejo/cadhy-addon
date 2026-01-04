"""
CFD Export Templates
Pre-configured export templates for common CFD solvers.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class CFDSolver(Enum):
    """Supported CFD solvers."""

    OPENFOAM = "openfoam"
    ANSYS_FLUENT = "ansys_fluent"
    STAR_CCM = "star_ccm"
    FLOW3D = "flow3d"
    SIMSCALE = "simscale"
    GENERIC = "generic"


@dataclass
class CFDExportTemplate:
    """CFD export template configuration."""

    name: str
    solver: CFDSolver
    format: str  # stl, obj, etc.
    ascii: bool  # ASCII vs binary
    scale: float  # Unit scale factor
    flip_normals: bool  # Some solvers expect outward normals
    split_patches: bool  # Export patches as separate files
    create_structure: bool  # Create solver folder structure
    notes: str  # Usage notes


# Pre-defined templates
TEMPLATES: Dict[str, CFDExportTemplate] = {
    "openfoam_snappy": CFDExportTemplate(
        name="OpenFOAM (snappyHexMesh)",
        solver=CFDSolver.OPENFOAM,
        format="stl",
        ascii=True,  # OpenFOAM prefers ASCII STL for snappyHexMesh
        scale=1.0,  # Assuming meters
        flip_normals=False,
        split_patches=True,  # Separate STL for each patch
        create_structure=True,  # Create constant/triSurface/ structure
        notes="For snappyHexMesh. Place STL files in constant/triSurface/",
    ),
    "openfoam_cfmesh": CFDExportTemplate(
        name="OpenFOAM (cfMesh)",
        solver=CFDSolver.OPENFOAM,
        format="stl",
        ascii=True,
        scale=1.0,
        flip_normals=False,
        split_patches=True,
        create_structure=True,
        notes="For cfMesh. Place STL files in constant/triSurface/",
    ),
    "ansys_fluent": CFDExportTemplate(
        name="ANSYS Fluent",
        solver=CFDSolver.ANSYS_FLUENT,
        format="stl",
        ascii=False,  # Binary for performance
        scale=1.0,
        flip_normals=False,
        split_patches=False,  # Single mesh, patches via names
        create_structure=False,
        notes="Import into Fluent Meshing or SpaceClaim for mesh generation",
    ),
    "star_ccm": CFDExportTemplate(
        name="STAR-CCM+",
        solver=CFDSolver.STAR_CCM,
        format="stl",
        ascii=False,
        scale=1.0,
        flip_normals=False,
        split_patches=True,  # Separate regions
        create_structure=False,
        notes="Import as surface mesh for volume meshing",
    ),
    "flow3d": CFDExportTemplate(
        name="FLOW-3D",
        solver=CFDSolver.FLOW3D,
        format="stl",
        ascii=True,  # FLOW-3D prefers ASCII
        scale=1.0,
        flip_normals=True,  # FLOW-3D uses inward normals for solid
        split_patches=False,
        create_structure=False,
        notes="Import as solid geometry in FLOW-3D",
    ),
    "simscale": CFDExportTemplate(
        name="SimScale",
        solver=CFDSolver.SIMSCALE,
        format="stl",
        ascii=False,  # Binary for upload
        scale=1.0,
        flip_normals=False,
        split_patches=False,
        create_structure=False,
        notes="Upload to SimScale platform for cloud CFD",
    ),
    "generic": CFDExportTemplate(
        name="Generic CFD",
        solver=CFDSolver.GENERIC,
        format="stl",
        ascii=False,
        scale=1.0,
        flip_normals=False,
        split_patches=False,
        create_structure=False,
        notes="Standard STL export for any CFD software",
    ),
}


def get_template(template_id: str) -> Optional[CFDExportTemplate]:
    """Get export template by ID."""
    return TEMPLATES.get(template_id)


def get_template_list() -> List[tuple]:
    """Get list of templates for Blender EnumProperty."""
    return [(key, template.name, template.notes) for key, template in TEMPLATES.items()]


def create_openfoam_structure(base_dir: str, case_name: str = "channel") -> Dict[str, str]:
    """
    Create OpenFOAM case directory structure.

    Args:
        base_dir: Base directory
        case_name: Case folder name

    Returns:
        Dictionary with created paths
    """
    case_dir = os.path.join(base_dir, case_name)
    paths = {
        "case": case_dir,
        "constant": os.path.join(case_dir, "constant"),
        "triSurface": os.path.join(case_dir, "constant", "triSurface"),
        "system": os.path.join(case_dir, "system"),
        "0": os.path.join(case_dir, "0"),
    }

    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    return paths


def generate_openfoam_mesh_dict(
    stl_files: List[str],
    patch_info: Dict[str, str],
    output_path: str,
) -> str:
    """
    Generate snappyHexMeshDict content.

    Args:
        stl_files: List of STL filenames
        patch_info: Dictionary mapping patch names to types
        output_path: Output file path

    Returns:
        Generated dictionary content
    """
    # Basic snappyHexMeshDict structure
    content = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{{
"""

    # Add geometry entries
    for stl_file in stl_files:
        name = os.path.splitext(os.path.basename(stl_file))[0]
        content += f"""    {name}
    {{
        type triSurfaceMesh;
        file "{os.path.basename(stl_file)}";
    }}
"""

    content += """};

castellatedMeshControls
{
    maxLocalCells       100000;
    maxGlobalCells      2000000;
    minRefinementCells  10;
    maxLoadUnbalance    0.10;
    nCellsBetweenLevels 3;

    features
    (
    );

    refinementSurfaces
    {
"""

    # Add refinement surface entries
    for stl_file in stl_files:
        name = os.path.splitext(os.path.basename(stl_file))[0]
        patch_type = patch_info.get(name, "wall")
        content += f"""        {name}
        {{
            level (2 2);
            patchInfo
            {{
                type {patch_type};
            }}
        }}
"""

    content += """    };

    resolveFeatureAngle 30;
    refinementRegions
    {
    };

    locationInMesh (0 0 0.5);
    allowFreeStandingZoneFaces true;
}

snapControls
{
    nSmoothPatch    3;
    tolerance       2.0;
    nSolveIter      30;
    nRelaxIter      5;
    nFeatureSnapIter 10;
}

addLayersControls
{
    relativeSizes   true;
    layers
    {
    };
    expansionRatio  1.0;
    finalLayerThickness 0.3;
    minThickness    0.1;
    nGrow           0;
    featureAngle    60;
    nRelaxIter      3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals  3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter      50;
}

meshQualityControls
{
    maxNonOrtho     65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave      80;
    minVol          1e-13;
    minTetQuality   -1e30;
    minArea         -1;
    minTwist        0.02;
    minDeterminant  0.001;
    minFaceWeight   0.05;
    minVolRatio     0.01;
    minTriangleTwist -1;
    nSmoothScale    4;
    errorReduction  0.75;
}

mergeTolerance 1e-6;

// ************************************************************************* //
"""

    # Write file
    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_blockmesh_dict(
    bbox: tuple,
    cell_size: float,
    output_path: str,
) -> str:
    """
    Generate blockMeshDict for background mesh.

    Args:
        bbox: Bounding box (min_x, min_y, min_z, max_x, max_y, max_z)
        cell_size: Target cell size
        output_path: Output file path

    Returns:
        Generated dictionary content
    """
    min_x, min_y, min_z, max_x, max_y, max_z = bbox

    # Add padding
    pad = cell_size * 2
    min_x -= pad
    min_y -= pad
    min_z -= pad
    max_x += pad
    max_y += pad
    max_z += pad

    # Calculate cell counts
    nx = max(1, int((max_x - min_x) / cell_size))
    ny = max(1, int((max_y - min_y) / cell_size))
    nz = max(1, int((max_z - min_z) / cell_size))

    content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

scale 1;

vertices
(
    ({min_x:.6f} {min_y:.6f} {min_z:.6f})
    ({max_x:.6f} {min_y:.6f} {min_z:.6f})
    ({max_x:.6f} {max_y:.6f} {min_z:.6f})
    ({min_x:.6f} {max_y:.6f} {min_z:.6f})
    ({min_x:.6f} {min_y:.6f} {max_z:.6f})
    ({max_x:.6f} {min_y:.6f} {max_z:.6f})
    ({max_x:.6f} {max_y:.6f} {max_z:.6f})
    ({min_x:.6f} {max_y:.6f} {max_z:.6f})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    allBoundary
    {{
        type patch;
        faces
        (
            (3 7 6 2)
            (0 4 7 3)
            (2 6 5 1)
            (1 5 4 0)
            (0 3 2 1)
            (4 5 6 7)
        );
    }}
);

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content
