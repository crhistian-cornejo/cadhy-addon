"""
Export PDF Report Module
Generate PDF reports for CADHY pre-design documentation.
Uses basic Python approach without external dependencies.
"""

from datetime import datetime
from typing import Any, Dict, Optional

# Try to import reportlab (optional dependency)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def is_pdf_available() -> bool:
    """Check if PDF export is available."""
    return HAS_REPORTLAB


def generate_pdf_report(
    report_data: Dict[str, Any],
    filepath: str,
    include_sections_table: bool = True,
    include_hydraulics: bool = True,
    logo_path: Optional[str] = None,
) -> bool:
    """
    Generate PDF report from project data.

    Args:
        report_data: Dictionary with project report data
        filepath: Output file path
        include_sections_table: Include detailed sections table
        include_hydraulics: Include hydraulic calculations
        logo_path: Optional path to company logo

    Returns:
        True if successful, False otherwise
    """
    if not HAS_REPORTLAB:
        print("PDF export requires 'reportlab' package. Install with: pip install reportlab")
        return False

    try:
        if not filepath.lower().endswith(".pdf"):
            filepath += ".pdf"

        doc = SimpleDocTemplate(
            filepath, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
        )

        # Build story (content elements)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
        )

        heading_style = ParagraphStyle(
            "CustomHeading", parent=styles["Heading2"], fontSize=14, spaceBefore=20, spaceAfter=10
        )

        normal_style = styles["Normal"]

        # Title
        story.append(Paragraph("CADHY Pre-Design Report", title_style))
        story.append(Spacer(1, 0.5 * cm))

        # Project info
        project = report_data.get("project", {})
        story.append(
            Paragraph(
                f"<b>Project:</b> {project.get('name', 'CADHY Project')}<br/>"
                f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
                f"<b>Generator:</b> CADHY Blender Add-on",
                normal_style,
            )
        )

        story.append(Spacer(1, 1 * cm))

        # Axis Information
        story.append(Paragraph("1. Axis Information", heading_style))
        axis = report_data.get("axis", {})
        axis_data = [
            ["Property", "Value", "Unit"],
            ["Axis Name", str(axis.get("name", "N/A")), ""],
            ["Total Length", f"{axis.get('total_length_m', 0):.2f}", "m"],
        ]
        axis_table = Table(axis_data, colWidths=[6 * cm, 6 * cm, 3 * cm])
        axis_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(axis_table)

        story.append(Spacer(1, 0.5 * cm))

        # Channel Parameters
        story.append(Paragraph("2. Channel Cross-Section", heading_style))
        channel = report_data.get("channel", {})
        channel_data = [
            ["Parameter", "Value", "Unit"],
            ["Section Type", str(channel.get("section_type", "N/A")), ""],
            ["Bottom Width", f"{channel.get('bottom_width_m', 0):.3f}", "m"],
            ["Side Slope", f"{channel.get('side_slope', 0):.2f}:1", "H:V"],
            ["Design Height", f"{channel.get('height_m', 0):.3f}", "m"],
            ["Freeboard", f"{channel.get('freeboard_m', 0):.3f}", "m"],
            ["Total Height", f"{channel.get('total_height_m', 0):.3f}", "m"],
            ["Top Width", f"{channel.get('top_width_m', 0):.3f}", "m"],
            ["Lining Thickness", f"{channel.get('lining_thickness_m', 0):.3f}", "m"],
        ]
        channel_table = Table(channel_data, colWidths=[6 * cm, 6 * cm, 3 * cm])
        channel_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(channel_table)

        story.append(Spacer(1, 0.5 * cm))

        # CFD Domain (if available)
        if "cfd_domain" in report_data:
            story.append(Paragraph("3. CFD Domain", heading_style))
            cfd = report_data["cfd_domain"]
            cfd_data = [
                ["Property", "Value", "Status"],
                ["Volume", f"{cfd.get('volume_m3', 0):.3f} m³", ""],
                ["Watertight", "", "Yes" if cfd.get("is_watertight") else "No"],
                ["Valid for CFD", "", "Yes" if cfd.get("is_valid") else "No"],
                ["Non-manifold Edges", str(cfd.get("non_manifold_edges", 0)), ""],
            ]
            cfd_table = Table(cfd_data, colWidths=[6 * cm, 5 * cm, 4 * cm])
            cfd_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(cfd_table)

            # Patch areas table
            if cfd.get("patch_areas_m2"):
                story.append(Spacer(1, 0.3 * cm))
                story.append(Paragraph("<b>Boundary Patches:</b>", normal_style))
                patch_data = [["Patch Name", "Area (m²)"]]
                for patch, area in cfd["patch_areas_m2"].items():
                    patch_data.append([patch, f"{area:.4f}"])

                patch_table = Table(patch_data, colWidths=[8 * cm, 7 * cm])
                patch_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ]
                    )
                )
                story.append(patch_table)

            story.append(Spacer(1, 0.5 * cm))

        # Sections (if available)
        if "sections" in report_data and include_sections_table:
            story.append(Paragraph("4. Cross-Sections Summary", heading_style))
            sections = report_data["sections"]

            story.append(Paragraph(f"<b>Number of Sections:</b> {sections.get('count', 0)}", normal_style))

            if sections.get("hydraulic_areas_m2"):
                areas = sections["hydraulic_areas_m2"]
                avg_area = sum(areas) / len(areas) if areas else 0
                story.append(Paragraph(f"<b>Average Hydraulic Area:</b> {avg_area:.4f} m²", normal_style))

            if sections.get("wetted_perimeters_m"):
                perimeters = sections["wetted_perimeters_m"]
                avg_wp = sum(perimeters) / len(perimeters) if perimeters else 0
                story.append(Paragraph(f"<b>Average Wetted Perimeter:</b> {avg_wp:.3f} m", normal_style))

            story.append(Spacer(1, 0.3 * cm))

            # Sections table (first 20 sections)
            if sections.get("stations"):
                stations = sections["stations"]
                areas = sections.get("hydraulic_areas_m2", [0] * len(stations))
                perimeters = sections.get("wetted_perimeters_m", [0] * len(stations))

                sections_table_data = [["Station (m)", "Area (m²)", "Wetted P. (m)", "Hyd. Radius (m)"]]

                for i, (sta, area, wp) in enumerate(zip(stations, areas, perimeters)):
                    if i >= 20:  # Limit to first 20
                        sections_table_data.append(["...", "...", "...", "..."])
                        break
                    hr = area / wp if wp > 0 else 0
                    sections_table_data.append([f"{sta:.2f}", f"{area:.4f}", f"{wp:.3f}", f"{hr:.4f}"])

                sect_table = Table(sections_table_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
                sect_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.darkorange),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                        ]
                    )
                )
                story.append(sect_table)

        # Footer
        story.append(Spacer(1, 2 * cm))
        story.append(
            Paragraph(
                "<i>This report was automatically generated by CADHY Blender Add-on. "
                "Please verify all values before final design.</i>",
                ParagraphStyle("Footer", parent=normal_style, fontSize=8, textColor=colors.grey),
            )
        )

        # Build PDF
        doc.build(story)
        return True

    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback

        traceback.print_exc()
        return False


def export_pdf_fallback(report_data: Dict[str, Any], filepath: str) -> bool:
    """
    Fallback PDF export using basic file write (creates HTML that can be printed to PDF).

    Args:
        report_data: Dictionary with project report data
        filepath: Output file path

    Returns:
        True if successful
    """
    try:
        # Generate HTML that can be opened and printed to PDF
        html_path = filepath.replace(".pdf", ".html")
        if not html_path.endswith(".html"):
            html_path += ".html"

        html_content = generate_html_report(report_data)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML report saved to: {html_path}")
        print("Open in browser and print to PDF (Ctrl+P)")
        return True

    except Exception as e:
        print(f"HTML export error: {e}")
        return False


def generate_html_report(report_data: Dict[str, Any]) -> str:
    """Generate HTML version of the report."""
    project = report_data.get("project", {})
    axis = report_data.get("axis", {})
    channel = report_data.get("channel", {})

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CADHY Pre-Design Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #ecf0f1; }}
        .info {{ color: #7f8c8d; font-size: 12px; }}
        .footer {{ margin-top: 40px; font-size: 10px; color: #95a5a6; text-align: center; }}
    </style>
</head>
<body>
    <h1>CADHY Pre-Design Report</h1>

    <p class="info">
        <b>Project:</b> {project.get("name", "CADHY Project")}<br>
        <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}<br>
        <b>Generator:</b> CADHY Blender Add-on
    </p>

    <h2>1. Axis Information</h2>
    <table>
        <tr><th>Property</th><th>Value</th><th>Unit</th></tr>
        <tr><td>Axis Name</td><td>{axis.get("name", "N/A")}</td><td></td></tr>
        <tr><td>Total Length</td><td>{axis.get("total_length_m", 0):.2f}</td><td>m</td></tr>
    </table>

    <h2>2. Channel Cross-Section</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
        <tr><td>Section Type</td><td>{channel.get("section_type", "N/A")}</td><td></td></tr>
        <tr><td>Bottom Width</td><td>{channel.get("bottom_width_m", 0):.3f}</td><td>m</td></tr>
        <tr><td>Side Slope</td><td>{channel.get("side_slope", 0):.2f}:1</td><td>H:V</td></tr>
        <tr><td>Design Height</td><td>{channel.get("height_m", 0):.3f}</td><td>m</td></tr>
        <tr><td>Freeboard</td><td>{channel.get("freeboard_m", 0):.3f}</td><td>m</td></tr>
        <tr><td>Total Height</td><td>{channel.get("total_height_m", 0):.3f}</td><td>m</td></tr>
        <tr><td>Top Width</td><td>{channel.get("top_width_m", 0):.3f}</td><td>m</td></tr>
        <tr><td>Lining Thickness</td><td>{channel.get("lining_thickness_m", 0):.3f}</td><td>m</td></tr>
    </table>
"""

    # Add CFD section if available
    if "cfd_domain" in report_data:
        cfd = report_data["cfd_domain"]
        html += f"""
    <h2>3. CFD Domain</h2>
    <table>
        <tr><th>Property</th><th>Value</th><th>Status</th></tr>
        <tr><td>Volume</td><td>{cfd.get("volume_m3", 0):.3f} m³</td><td></td></tr>
        <tr><td>Watertight</td><td></td><td>{"Yes" if cfd.get("is_watertight") else "No"}</td></tr>
        <tr><td>Valid for CFD</td><td></td><td>{"Yes" if cfd.get("is_valid") else "No"}</td></tr>
    </table>
"""

    html += """
    <div class="footer">
        <p>This report was automatically generated by CADHY Blender Add-on.<br>
        Please verify all values before final design.</p>
    </div>
</body>
</html>
"""
    return html
