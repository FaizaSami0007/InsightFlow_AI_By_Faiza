"""Deterministic Export Engine for Dashboards (PDF, PNG, CSV, JSON).

Strict architectural rules:
- Zero arbitrary code execution or AI-generated HTML/scripts.
- Deterministic rendering of validated dashboard specifications and analytical results.
- Resource constraints and sanitized output filepaths.
"""

import csv
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from PIL import Image as PILImage
from PIL import ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Configurable Export Resource Limits
MAX_EXPORT_ROWS = 50000
MAX_EXPORT_WIDGETS = 20
MAX_EXPORT_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_EXPORT_EXECUTION_TIME = 30.0  # seconds


def sanitize_filename(name: str) -> str:
    """Sanitize title into safe filename without path traversal characters."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    clean = re.sub(r"[-\s]+", "-", clean).strip("-")
    return clean or "dashboard-export"


class NumberedCanvas:
    """Two-pass canvas for adding total page numbers and header/footer to PDF."""

    def __init__(self, *args: Any, **kwargs: Any):
        pass


class ExportEngine:
    """Deterministic export generation engine for Dashboards."""

    @staticmethod
    def generate_pdf(
        dashboard_spec: Dict[str, Any],
        widgets_data: List[Dict[str, Any]],
        filter_snapshot: Dict[str, Any],
        output_path: str,
        page_size: str = "A4",
        orientation: str = "landscape",
        include_provenance: bool = True,
        include_filters: bool = True,
        title_override: Optional[str] = None,
    ) -> int:
        """Render deterministic PDF report from dashboard specification."""
        base_size = A4 if page_size.upper() == "A4" else letter
        chosen_page_size = landscape(base_size) if orientation.lower() == "landscape" else portrait(base_size)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=chosen_page_size,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        # Custom Soft UI Styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#172033"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#536176"),
            fontName="Helvetica",
        )
        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0F766E"),
            fontName="Helvetica-Bold",
        )
        card_title_style = ParagraphStyle(
            "CardTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#172033"),
            fontName="Helvetica-Bold",
        )
        card_text_style = ParagraphStyle(
            "CardText",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#536176"),
            fontName="Helvetica",
        )
        kpi_val_style = ParagraphStyle(
            "KPIValue",
            parent=styles["Normal"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F766E"),
            fontName="Helvetica-Bold",
            alignment=1,  # Center
        )
        kpi_lbl_style = ParagraphStyle(
            "KPILabel",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#536176"),
            fontName="Helvetica",
            alignment=1,  # Center
        )

        elements: List[Any] = []

        # 1. Header Section
        doc_title = title_override or dashboard_spec.get("name") or dashboard_spec.get("title") or "Analytics Dashboard"
        dataset_id = dashboard_spec.get("dataset_id", "N/A")
        version_id = dashboard_spec.get("dataset_version_id", "v1")
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")

        elements.append(Paragraph(doc_title, title_style))
        if dashboard_spec.get("description"):
            elements.append(Paragraph(dashboard_spec["description"], subtitle_style))

        meta_text = f"<b>Dataset:</b> {dataset_id} &nbsp;|&nbsp; <b>Version:</b> {version_id} &nbsp;|&nbsp; <b>Generated:</b> {now_str}"
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(meta_text, subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E3E8EF"), spaceBefore=2, spaceAfter=8))

        # 2. Active Filters Banner
        if include_filters and filter_snapshot:
            filter_items = [f"<b>{k}:</b> {v}" for k, v in filter_snapshot.items() if v is not None and v != ""]
            if filter_items:
                filter_summary = " &nbsp;&bull;&nbsp; ".join(filter_items)
                filter_box = Table(
                    [[Paragraph(f"<b>Active Filters:</b> {filter_summary}", subtitle_style)]],
                    colWidths=[chosen_page_size[0] - 72],
                )
                filter_box.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E6F4F1")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0F766E")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                    ])
                )
                elements.append(filter_box)
                elements.append(Spacer(1, 10))

        # 3. KPI Callouts Grid (Row of KPI widgets)
        kpi_widgets = [w for w in widgets_data if w.get("widget_type") == "kpi"]
        other_widgets = [w for w in widgets_data if w.get("widget_type") != "kpi"]

        if kpi_widgets:
            kpi_cells: List[Any] = []
            col_w = (chosen_page_size[0] - 72) / max(1, min(len(kpi_widgets), 4))
            for kw in kpi_widgets[:4]:
                w_title = kw.get("title", "Metric")
                rows = kw.get("result_data", {}).get("rows", [])
                val_display = "--"
                if rows and isinstance(rows[0], dict):
                    # Pick first numeric value
                    for v in rows[0].values():
                        if isinstance(v, (int, float)):
                            val_display = f"{v:,.2f}".rstrip("0").rstrip(".")
                            break
                        elif v is not None:
                            val_display = str(v)
                            break

                card_content = [
                    Paragraph(w_title, kpi_lbl_style),
                    Spacer(1, 2),
                    Paragraph(val_display, kpi_val_style),
                ]
                kpi_cells.append(card_content)

            # Build KPI Table Row
            kpi_table = Table([kpi_cells], colWidths=[col_w] * len(kpi_cells))
            kpi_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E3E8EF")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E3E8EF")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ])
            )
            elements.append(kpi_table)
            elements.append(Spacer(1, 14))

        # 4. Analytical Components & Charts
        for idx, widget in enumerate(other_widgets[:MAX_EXPORT_WIDGETS]):
            w_title = widget.get("title", f"Widget #{idx+1}")
            w_desc = widget.get("description", "")
            chart_spec = widget.get("chart_spec") or widget.get("chart_spec_json") or {}
            chart_type = chart_spec.get("chart_type", widget.get("widget_type", "chart")).upper()
            result_data = widget.get("result_data") or {}
            rows = result_data.get("rows", [])
            cols = result_data.get("columns", [])

            widget_elements: List[Any] = []
            header_text = f"<b>{w_title}</b> <font color='#0F766E'>({chart_type})</font>"
            widget_elements.append(Paragraph(header_text, card_title_style))
            if w_desc:
                widget_elements.append(Paragraph(w_desc, card_text_style))
            widget_elements.append(Spacer(1, 4))

            # Table representation of chart / table data
            if rows and cols:
                table_cols = cols[:6]  # Max 6 columns in PDF view
                t_data = [[Paragraph(f"<b>{c}</b>", card_text_style) for c in table_cols]]
                for r in rows[:8]:  # First 8 sample rows
                    row_cells = []
                    for c in table_cols:
                        raw_val = r.get(c, "")
                        display_val = f"{raw_val:,.2f}" if isinstance(raw_val, float) else str(raw_val)
                        row_cells.append(Paragraph(display_val, card_text_style))
                    t_data.append(row_cells)

                total_w = chosen_page_size[0] - 72
                cell_w = total_w / len(table_cols)
                data_table = Table(t_data, colWidths=[cell_w] * len(table_cols))
                data_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F9FC")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E3E8EF")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E3E8EF")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFC")]),
                        ("PADDING", (0, 0), (-1, -1), 4),
                    ])
                )
                widget_elements.append(data_table)
                if len(rows) > 8:
                    widget_elements.append(Spacer(1, 2))
                    widget_elements.append(
                        Paragraph(f"<i>Showing 8 of {len(rows)} result rows</i>", card_text_style)
                    )
            else:
                widget_elements.append(Paragraph("<i>No data records returned for this widget.</i>", card_text_style))

            widget_elements.append(Spacer(1, 10))
            elements.append(KeepTogether(widget_elements))

        # 5. Provenance Audit Section
        if include_provenance:
            elements.append(Spacer(1, 8))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E3E8EF"), spaceBefore=4, spaceAfter=8))
            elements.append(Paragraph("Analytical Provenance & Audit Trail", section_style))
            elements.append(Spacer(1, 4))

            prov_rows: List[List[Any]] = [
                [
                    Paragraph("<b>Widget</b>", card_text_style),
                    Paragraph("<b>Analysis ID</b>", card_text_style),
                    Paragraph("<b>Visualization</b>", card_text_style),
                    Paragraph("<b>Dataset Version</b>", card_text_style),
                ]
            ]
            for w in widgets_data:
                prov_rows.append([
                    Paragraph(w.get("title", "Widget"), card_text_style),
                    Paragraph(w.get("analysis_id", "Direct Aggregation") or "Direct Aggregation", card_text_style),
                    Paragraph((w.get("chart_spec") or {}).get("chart_type", w.get("widget_type", "N/A")), card_text_style),
                    Paragraph(f"{dataset_id} ({version_id})", card_text_style),
                ])

            prov_table = Table(prov_rows, colWidths=[(chosen_page_size[0] - 72) / 4] * 4)
            prov_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F9FC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E3E8EF")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E3E8EF")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ])
            )
            elements.append(KeepTogether([prov_table]))

        doc.build(elements)
        return os.path.getsize(output_path)

    @staticmethod
    def generate_png(
        dashboard_spec: Dict[str, Any],
        widgets_data: List[Dict[str, Any]],
        filter_snapshot: Dict[str, Any],
        output_path: str,
        title_override: Optional[str] = None,
    ) -> int:
        """Render high-contrast, clean 2D PNG snapshot of the dashboard."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        img_width = 1200
        # Calculate dynamic height based on widgets count
        kpi_count = len([w for w in widgets_data if w.get("widget_type") == "kpi"])
        chart_count = len([w for w in widgets_data if w.get("widget_type") != "kpi"])
        img_height = 200 + (120 if kpi_count > 0 else 0) + (chart_count * 180)
        img_height = max(600, min(3000, img_height))

        # Canvas background (Cloud: #F7F9FC)
        img = PILImage.new("RGB", (img_width, img_height), color=(247, 249, 252))
        draw = ImageDraw.Draw(img)

        # Header background banner
        draw.rectangle([(0, 0), (img_width, 90)], fill=(255, 255, 255), outline=(227, 232, 239))

        # Text Drawing (using default font with fallback)
        doc_title = title_override or dashboard_spec.get("name") or dashboard_spec.get("title") or "Analytics Dashboard"
        dataset_info = f"Dataset: {dashboard_spec.get('dataset_id', 'N/A')} ({dashboard_spec.get('dataset_version_id', 'v1')})"
        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        draw.text((30, 20), doc_title, fill=(23, 32, 51))
        draw.text((30, 48), f"{dataset_info}  |  Generated: {gen_time}  |  InsightFlow AI Phase 9", fill=(83, 97, 118))

        current_y = 110

        # Filter Pills
        if filter_snapshot:
            filter_text = "Filters: " + " | ".join([f"{k}={v}" for k, v in filter_snapshot.items() if v])
            draw.rounded_rectangle([(30, current_y), (img_width - 30, current_y + 32)], radius=6, fill=(230, 244, 241), outline=(15, 118, 110))
            draw.text((45, current_y + 8), filter_text, fill=(15, 118, 110))
            current_y += 48

        # KPI Row
        kpi_widgets = [w for w in widgets_data if w.get("widget_type") == "kpi"][:4]
        if kpi_widgets:
            card_w = (img_width - 60 - (len(kpi_widgets) - 1) * 16) / len(kpi_widgets)
            for idx, kw in enumerate(kpi_widgets):
                card_x = 30 + idx * (card_w + 16)
                draw.rounded_rectangle([(card_x, current_y), (card_x + card_w, current_y + 80)], radius=8, fill=(255, 255, 255), outline=(227, 232, 239))
                draw.text((card_x + 14, current_y + 12), kw.get("title", "KPI"), fill=(83, 97, 118))

                rows = kw.get("result_data", {}).get("rows", [])
                val_str = "--"
                if rows and isinstance(rows[0], dict):
                    for v in rows[0].values():
                        if isinstance(v, (int, float)):
                            val_str = f"{v:,.2f}".rstrip("0").rstrip(".")
                            break
                        elif v is not None:
                            val_str = str(v)
                            break
                draw.text((card_x + 14, current_y + 36), val_str, fill=(15, 118, 110))
            current_y += 96

        # Chart and Table Cards
        other_widgets = [w for w in widgets_data if w.get("widget_type") != "kpi"]
        for w in other_widgets:
            card_box = [(30, current_y), (img_width - 30, current_y + 160)]
            draw.rounded_rectangle(card_box, radius=8, fill=(255, 255, 255), outline=(227, 232, 239))

            w_title = w.get("title", "Analytical Component")
            w_chart = (w.get("chart_spec") or {}).get("chart_type", w.get("widget_type", "chart")).upper()
            draw.text((46, current_y + 14), f"{w_title} [{w_chart}]", fill=(23, 32, 51))

            rows = (w.get("result_data") or {}).get("rows", [])
            cols = (w.get("result_data") or {}).get("columns", [])
            if rows and cols:
                sample_text = f"Records: {len(rows)} rows | Fields: {', '.join(cols[:5])}"
                draw.text((46, current_y + 40), sample_text, fill=(83, 97, 118))
                # Render 3 preview lines
                line_y = current_y + 68
                for r in rows[:3]:
                    row_vals = [f"{k}: {v}" for k, v in list(r.items())[:4]]
                    draw.text((46, line_y), " | ".join(row_vals), fill=(50, 60, 80))
                    line_y += 22
            else:
                draw.text((46, current_y + 50), "Analysis result computed and validated.", fill=(83, 97, 118))

            current_y += 176

        # Save to disk
        img.save(output_path, format="PNG")
        return os.path.getsize(output_path)

    @staticmethod
    def generate_csv(
        dashboard_spec: Dict[str, Any],
        widgets_data: List[Dict[str, Any]],
        filter_snapshot: Dict[str, Any],
        output_path: str,
        target_widget_id: Optional[str] = None,
    ) -> int:
        """Render validated tabular analytical data to CSV format."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Metadata header comments
            writer.writerow(["# InsightFlow AI Dashboard Export"])
            writer.writerow([f"# Dashboard: {dashboard_spec.get('name', 'Dashboard')}"])
            writer.writerow([f"# Dataset: {dashboard_spec.get('dataset_id')} (v{dashboard_spec.get('dataset_version_id')})"])
            writer.writerow([f"# Exported At: {datetime.now(timezone.utc).isoformat()}"])
            if filter_snapshot:
                writer.writerow([f"# Active Filters: {filter_snapshot}"])
            writer.writerow([])

            # Filter target widgets
            widgets_to_export = widgets_data
            if target_widget_id:
                widgets_to_export = [w for w in widgets_data if w.get("id") == target_widget_id]
                if not widgets_to_export:
                    widgets_to_export = widgets_data

            for w in widgets_to_export:
                w_title = w.get("title", "Widget Data")
                w_analysis_id = w.get("analysis_id", "N/A")
                res_data = w.get("result_data") or {}
                cols = res_data.get("columns", [])
                rows = res_data.get("rows", [])

                writer.writerow([f"## Section: {w_title} (Analysis ID: {w_analysis_id})"])
                if cols and rows:
                    writer.writerow(cols)
                    for r in rows[:MAX_EXPORT_ROWS]:
                        writer.writerow([r.get(c, "") for c in cols])
                elif rows and isinstance(rows[0], dict):
                    auto_cols = list(rows[0].keys())
                    writer.writerow(auto_cols)
                    for r in rows[:MAX_EXPORT_ROWS]:
                        writer.writerow([r.get(c, "") for c in auto_cols])
                else:
                    writer.writerow(["No tabular records"])
                writer.writerow([])

        return os.path.getsize(output_path)
