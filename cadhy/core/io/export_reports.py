"""
Export Reports Module
Generate and export reports for CADHY data.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from ..model.cfd_params import CFDDomainInfo
from ..model.channel_params import ChannelParams
from ..model.sections_params import SectionsReport


def export_sections_csv(report: SectionsReport, filepath: str) -> bool:
    """
    Export sections report to CSV.

    Args:
        report: SectionsReport object
        filepath: Output file path

    Returns:
        True if successful
    """
    try:
        if not filepath.lower().endswith(".csv"):
            filepath += ".csv"

        csv_content = report.to_csv()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)

        return True
    except Exception as e:
        print(f"CSV export error: {e}")
        return False


def export_sections_json(report: SectionsReport, filepath: str) -> bool:
    """
    Export sections report to JSON.

    Args:
        report: SectionsReport object
        filepath: Output file path

    Returns:
        True if successful
    """
    try:
        if not filepath.lower().endswith(".json"):
            filepath += ".json"

        data = report.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return True
    except Exception as e:
        print(f"JSON export error: {e}")
        return False


def generate_project_report(
    channel_params: ChannelParams,
    cfd_info: Optional[CFDDomainInfo] = None,
    sections_report: Optional[SectionsReport] = None,
    axis_name: str = "",
    project_name: str = "CADHY Project",
) -> Dict[str, Any]:
    """
    Generate comprehensive project report.

    Args:
        channel_params: Channel parameters
        cfd_info: CFD domain information
        sections_report: Sections report
        axis_name: Name of axis curve
        project_name: Project name

    Returns:
        Dictionary with complete project data
    """
    report = {
        "project": {
            "name": project_name,
            "generated_at": datetime.now().isoformat(),
            "generator": "CADHY Blender Add-on",
            "version": "0.1.0",
        },
        "axis": {"name": axis_name, "total_length_m": sections_report.total_length if sections_report else 0},
        "channel": {
            "section_type": channel_params.section_type.value,
            "bottom_width_m": channel_params.bottom_width,
            "side_slope": channel_params.side_slope,
            "height_m": channel_params.height,
            "freeboard_m": channel_params.freeboard,
            "total_height_m": channel_params.total_height,
            "top_width_m": channel_params.top_width,
            "lining_thickness_m": channel_params.lining_thickness,
            "resolution_m": channel_params.resolution_m,
        },
    }

    # Add CFD info if available
    if cfd_info:
        report["cfd_domain"] = {
            "volume_m3": cfd_info.volume,
            "is_watertight": cfd_info.is_watertight,
            "is_valid": cfd_info.is_valid,
            "non_manifold_edges": cfd_info.non_manifold_edges,
            "self_intersections": cfd_info.self_intersections,
            "patch_areas_m2": cfd_info.patch_areas,
        }

    # Add sections summary if available
    if sections_report and sections_report.sections:
        report["sections"] = {
            "count": len(sections_report.sections),
            "stations": [s.station for s in sections_report.sections],
            "hydraulic_areas_m2": [s.hydraulic_area for s in sections_report.sections],
            "wetted_perimeters_m": [s.wetted_perimeter for s in sections_report.sections],
        }

    return report


def export_project_report(report: Dict[str, Any], filepath: str, format: str = "json") -> bool:
    """
    Export project report to file.

    Args:
        report: Report dictionary
        filepath: Output file path
        format: Output format ('json' or 'txt')

    Returns:
        True if successful
    """
    try:
        if format == "json":
            if not filepath.lower().endswith(".json"):
                filepath += ".json"

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        elif format == "txt":
            if not filepath.lower().endswith(".txt"):
                filepath += ".txt"

            lines = generate_text_report(report)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        return True
    except Exception as e:
        print(f"Report export error: {e}")
        return False


def generate_text_report(report: Dict[str, Any]) -> list:
    """
    Generate human-readable text report.

    Args:
        report: Report dictionary

    Returns:
        List of text lines
    """
    lines = [
        "=" * 60,
        "CADHY PROJECT REPORT",
        "=" * 60,
        "",
        f"Project: {report.get('project', {}).get('name', 'Unknown')}",
        f"Generated: {report.get('project', {}).get('generated_at', 'Unknown')}",
        "",
        "-" * 40,
        "AXIS INFORMATION",
        "-" * 40,
    ]

    axis = report.get("axis", {})
    lines.append(f"  Name: {axis.get('name', 'Unknown')}")
    lines.append(f"  Total Length: {axis.get('total_length_m', 0):.2f} m")

    lines.extend(
        [
            "",
            "-" * 40,
            "CHANNEL PARAMETERS",
            "-" * 40,
        ]
    )

    channel = report.get("channel", {})
    lines.append(f"  Section Type: {channel.get('section_type', 'Unknown')}")
    lines.append(f"  Bottom Width: {channel.get('bottom_width_m', 0):.3f} m")
    lines.append(f"  Side Slope: {channel.get('side_slope', 0):.2f}:1 (H:V)")
    lines.append(f"  Height: {channel.get('height_m', 0):.3f} m")
    lines.append(f"  Freeboard: {channel.get('freeboard_m', 0):.3f} m")
    lines.append(f"  Total Height: {channel.get('total_height_m', 0):.3f} m")
    lines.append(f"  Top Width: {channel.get('top_width_m', 0):.3f} m")
    lines.append(f"  Lining Thickness: {channel.get('lining_thickness_m', 0):.3f} m")

    if "cfd_domain" in report:
        lines.extend(
            [
                "",
                "-" * 40,
                "CFD DOMAIN",
                "-" * 40,
            ]
        )

        cfd = report["cfd_domain"]
        lines.append(f"  Volume: {cfd.get('volume_m3', 0):.3f} m³")
        lines.append(f"  Watertight: {'Yes' if cfd.get('is_watertight') else 'No'}")
        lines.append(f"  Valid for CFD: {'Yes' if cfd.get('is_valid') else 'No'}")

        if cfd.get("patch_areas_m2"):
            lines.append("  Patch Areas:")
            for patch, area in cfd["patch_areas_m2"].items():
                lines.append(f"    {patch}: {area:.3f} m²")

    if "sections" in report:
        lines.extend(
            [
                "",
                "-" * 40,
                "SECTIONS SUMMARY",
                "-" * 40,
            ]
        )

        sections = report["sections"]
        lines.append(f"  Number of Sections: {sections.get('count', 0)}")

        if sections.get("hydraulic_areas_m2"):
            avg_area = sum(sections["hydraulic_areas_m2"]) / len(sections["hydraulic_areas_m2"])
            lines.append(f"  Average Hydraulic Area: {avg_area:.4f} m²")

    lines.extend(
        [
            "",
            "=" * 60,
            "END OF REPORT",
            "=" * 60,
        ]
    )

    return lines
