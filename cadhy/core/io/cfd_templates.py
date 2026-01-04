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


def generate_u_file(
    patches: Dict[str, dict],
    output_path: str,
) -> str:
    """
    Generate 0/U (velocity field) file for OpenFOAM.

    Args:
        patches: Dictionary with patch names and BC settings
                 {'inlet': {'type': 'velocity', 'velocity': 1.0},
                  'outlet': {'type': 'pressure'},
                  'walls': {'type': 'no_slip'},
                  'top': {'type': 'symmetry'}}
        output_path: Output file path

    Returns:
        Generated file content
    """
    content = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
"""

    for patch_name, bc in patches.items():
        bc_type = bc.get("type", "no_slip")

        if bc_type == "velocity":
            velocity = bc.get("velocity", 1.0)
            content += f"""    {patch_name}
    {{
        type            fixedValue;
        value           uniform ({velocity} 0 0);
    }}
"""
        elif bc_type == "pressure" or bc_type == "outflow":
            content += f"""    {patch_name}
    {{
        type            zeroGradient;
    }}
"""
        elif bc_type == "no_slip":
            content += f"""    {patch_name}
    {{
        type            noSlip;
    }}
"""
        elif bc_type == "slip":
            content += f"""    {patch_name}
    {{
        type            slip;
    }}
"""
        elif bc_type == "symmetry":
            content += f"""    {patch_name}
    {{
        type            symmetryPlane;
    }}
"""
        else:
            # Default to no-slip wall
            content += f"""    {patch_name}
    {{
        type            noSlip;
    }}
"""

    content += """}

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_p_file(
    patches: Dict[str, dict],
    output_path: str,
) -> str:
    """
    Generate 0/p (pressure field) file for OpenFOAM.

    Args:
        patches: Dictionary with patch names and BC settings
        output_path: Output file path

    Returns:
        Generated file content
    """
    content = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
"""

    for patch_name, bc in patches.items():
        bc_type = bc.get("type", "no_slip")

        if bc_type == "velocity":
            content += f"""    {patch_name}
    {{
        type            zeroGradient;
    }}
"""
        elif bc_type == "pressure":
            pressure = bc.get("pressure", 0.0)
            content += f"""    {patch_name}
    {{
        type            fixedValue;
        value           uniform {pressure};
    }}
"""
        elif bc_type == "outflow":
            content += f"""    {patch_name}
    {{
        type            fixedValue;
        value           uniform 0;
    }}
"""
        elif bc_type in ("no_slip", "slip", "rough"):
            content += f"""    {patch_name}
    {{
        type            zeroGradient;
    }}
"""
        elif bc_type == "symmetry":
            content += f"""    {patch_name}
    {{
        type            symmetryPlane;
    }}
"""
        else:
            content += f"""    {patch_name}
    {{
        type            zeroGradient;
    }}
"""

    content += """}

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_control_dict(
    case_name: str,
    end_time: float,
    delta_t: float,
    write_interval: float,
    output_path: str,
) -> str:
    """
    Generate system/controlDict file for OpenFOAM.

    Args:
        case_name: Name of the case
        end_time: Simulation end time
        delta_t: Time step
        write_interval: Write interval
        output_path: Output file path

    Returns:
        Generated file content
    """
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
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon - Case: {case_name}

application     simpleFoam;

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         {end_time};

deltaT          {delta_t};

writeControl    timeStep;

writeInterval   {int(write_interval / delta_t)};

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_fvschemes(output_path: str) -> str:
    """
    Generate system/fvSchemes file for OpenFOAM.

    Args:
        output_path: Output file path

    Returns:
        Generated file content
    """
    content = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss upwind;
    div(phi,epsilon) bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

wallDist
{
    method          meshWave;
}

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_fvsolution(output_path: str) -> str:
    """
    Generate system/fvSolution file for OpenFOAM.

    Args:
        output_path: Output file path

    Returns:
        Generated file content
    """
    content = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-06;
        relTol          0.1;
        smoother        GaussSeidel;
    }

    U
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0.1;
    }

    k
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0.1;
    }

    epsilon
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0.1;
    }

    omega
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;

    residualControl
    {
        p               1e-4;
        U               1e-4;
        "(k|epsilon|omega)" 1e-4;
    }
}

relaxationFactors
{
    equations
    {
        U               0.7;
        k               0.7;
        epsilon         0.7;
        omega           0.7;
    }
    fields
    {
        p               0.3;
    }
}

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_transport_properties(
    nu: float,
    output_path: str,
) -> str:
    """
    Generate constant/transportProperties file for OpenFOAM.

    Args:
        nu: Kinematic viscosity (m^2/s)
        output_path: Output file path

    Returns:
        Generated file content
    """
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
    object      transportProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

transportModel  Newtonian;

nu              nu [ 0 2 -1 0 0 0 0 ] {nu:.6e};

// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_turbulence_properties(
    model: str,
    output_path: str,
) -> str:
    """
    Generate constant/turbulenceProperties file for OpenFOAM.

    Args:
        model: Turbulence model ('laminar', 'kEpsilon', 'kOmegaSST')
        output_path: Output file path

    Returns:
        Generated file content
    """
    if model == "laminar":
        sim_type = "laminar"
        ras_model = ""
    else:
        sim_type = "RAS"
        ras_model = f"""
RAS
{{
    RASModel        {model};
    turbulence      on;
    printCoeffs     on;
}}
"""

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
    object      turbulenceProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// Generated by CADHY Blender Addon

simulationType  {sim_type};
{ras_model}
// ************************************************************************* //
"""

    with open(output_path, "w") as f:
        f.write(content)

    return content


def export_openfoam_case(
    export_dir: str,
    case_name: str,
    stl_files: List[str],
    patches: Dict[str, dict],
    bbox: tuple,
    cell_size: float = 0.5,
    nu: float = 1e-6,
    turbulence_model: str = "kOmegaSST",
) -> Dict[str, str]:
    """
    Export complete OpenFOAM case with all required files.

    Args:
        export_dir: Base export directory
        case_name: Case name
        stl_files: List of STL file paths
        patches: Dictionary with patch names and BC settings
        bbox: Mesh bounding box
        cell_size: Target cell size for blockMesh
        nu: Kinematic viscosity
        turbulence_model: Turbulence model name

    Returns:
        Dictionary with paths to generated files
    """
    # Create directory structure
    paths = create_openfoam_structure(export_dir, case_name)

    generated_files = {}

    # Generate blockMeshDict
    blockmesh_path = os.path.join(paths["system"], "blockMeshDict")
    generate_blockmesh_dict(bbox, cell_size, blockmesh_path)
    generated_files["blockMeshDict"] = blockmesh_path

    # Generate snappyHexMeshDict
    patch_types = {}
    for name, bc in patches.items():
        bc_type = bc.get("type", "wall")
        if bc_type in ("velocity", "mass_flow"):
            patch_types[name] = "patch"
        elif bc_type in ("pressure", "outflow"):
            patch_types[name] = "patch"
        elif bc_type == "symmetry":
            patch_types[name] = "symmetryPlane"
        else:
            patch_types[name] = "wall"

    snappy_path = os.path.join(paths["system"], "snappyHexMeshDict")
    generate_openfoam_mesh_dict(stl_files, patch_types, snappy_path)
    generated_files["snappyHexMeshDict"] = snappy_path

    # Generate controlDict
    control_path = os.path.join(paths["system"], "controlDict")
    generate_control_dict(case_name, 1000, 1, 100, control_path)
    generated_files["controlDict"] = control_path

    # Generate fvSchemes
    schemes_path = os.path.join(paths["system"], "fvSchemes")
    generate_fvschemes(schemes_path)
    generated_files["fvSchemes"] = schemes_path

    # Generate fvSolution
    solution_path = os.path.join(paths["system"], "fvSolution")
    generate_fvsolution(solution_path)
    generated_files["fvSolution"] = solution_path

    # Generate 0/U
    u_path = os.path.join(paths["0"], "U")
    generate_u_file(patches, u_path)
    generated_files["U"] = u_path

    # Generate 0/p
    p_path = os.path.join(paths["0"], "p")
    generate_p_file(patches, p_path)
    generated_files["p"] = p_path

    # Generate transportProperties
    transport_path = os.path.join(paths["constant"], "transportProperties")
    generate_transport_properties(nu, transport_path)
    generated_files["transportProperties"] = transport_path

    # Generate turbulenceProperties
    turbulence_path = os.path.join(paths["constant"], "turbulenceProperties")
    generate_turbulence_properties(turbulence_model, turbulence_path)
    generated_files["turbulenceProperties"] = turbulence_path

    return generated_files
