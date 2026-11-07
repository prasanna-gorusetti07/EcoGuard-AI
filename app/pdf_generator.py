import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from app.config import REPORTS_DIR

def generate_complaint_pdf(complaint: Dict[str, Any], audit_trail: List[Dict[str, Any]]) -> str:
    """
    Generates an official Government-format Environmental Incident & Complaint Report.
    Uses ReportLab if available, or generates a styled HTML printable report fallback.
    Returns the file path.
    """
    complaint_id = complaint["complaint_id"]
    pdf_filename = f"Report_{complaint_id}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor("#065f46"), # Deep emerald
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=12
        )

        section_heading = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor("#1f2937"),
            leading=12
        )

        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor("#dc2626"),
            leading=11
        )

        story = []

        # Header Banner
        header_data = [
            [
                Paragraph("<b>ECOGUARD AI – ENVIRONMENTAL INCIDENT & AUDIT REPORT</b>", title_style),
                Paragraph(f"<b>REPORT ID:</b> {complaint_id}<br/><b>GENERATED:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Paragraph("Official Investigation Dossier | Illegal Waste Dumping & Rapid Escalation Protocol", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceAfter=12))

        # Basic Info Grid
        info_data = [
            [Paragraph("<b>Status:</b>", body_style), Paragraph(f"<font color='#059669'><b>{complaint.get('status', 'New')}</b></font>", body_style),
             Paragraph("<b>Severity:</b>", body_style), Paragraph(f"<b>{complaint.get('severity', 'Medium')}</b>", body_style)],
            [Paragraph("<b>Reporter:</b>", body_style), Paragraph(f"{complaint.get('reporter_type', 'Citizen')} ({complaint.get('reporter_name', 'Anonymous')})", body_style),
             Paragraph("<b>Date Logged:</b>", body_style), Paragraph(f"{complaint.get('created_at', 'N/A')}", body_style)],
            [Paragraph("<b>GPS Coordinates:</b>", body_style), Paragraph(f"{complaint.get('latitude', 0.0):.6f}, {complaint.get('longitude', 0.0):.6f}", body_style),
             Paragraph("<b>Escalation Level:</b>", body_style), Paragraph(f"Level {complaint.get('escalation_level', 0)} ({complaint.get('escalated_to') or 'Standard'})", body_style)],
            [Paragraph("<b>Location Address:</b>", body_style), Paragraph(f"{complaint.get('location_address', 'N/A')}", body_style),
             Paragraph("<b>Landmark:</b>", body_style), Paragraph(f"{complaint.get('landmark') or 'None specified'}", body_style)],
        ]
        info_table = Table(info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 10))

        # AI Analysis Findings
        story.append(Paragraph("AI-Assisted Environmental Analysis", section_heading))
        cats = complaint.get("categories", [])
        cats_str = ", ".join(cats) if isinstance(cats, list) else str(cats)
        
        ai_data = [
            [Paragraph("<b>Primary Category:</b>", body_style), Paragraph(f"<b>{complaint.get('primary_category', 'General Waste')}</b>", body_style)],
            [Paragraph("<b>Identified Constituents:</b>", body_style), Paragraph(cats_str, body_style)],
            [Paragraph("<b>Confidence Score:</b>", body_style), Paragraph(f"{int(float(complaint.get('confidence_score', 0.85)) * 100)}%", body_style)],
            [Paragraph("<b>Risk Assessment:</b>", body_style), Paragraph(complaint.get('risk_assessment', 'Standard environmental concern.'), body_style)],
            [Paragraph("<b>Ecological Impact:</b>", body_style), Paragraph(complaint.get('environmental_impact', 'Potential soil and surface pollution.'), body_style)],
            [Paragraph("<b>Recommended Action:</b>", body_style), Paragraph(complaint.get('recommended_action', 'Sanitary squad dispatch for clearance.'), body_style)],
        ]
        ai_table = Table(ai_data, colWidths=[1.8 * inch, 5.2 * inch])
        ai_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#ecfdf5")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(ai_table)
        
        # Uncertainty Disclaimer
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>LEGAL NOTICE:</b> AI observations are preliminary and indicative. Physical verification and laboratory soil/water assays by certified authorities are mandatory before statutory enforcement.", disclaimer_style))
        story.append(Spacer(1, 10))

        # Officer & Action Status
        story.append(Paragraph("Inspection & Administrative Action Record", section_heading))
        officer_data = [
            [Paragraph("<b>Assigned Department:</b>", body_style), Paragraph(complaint.get('assigned_department', 'Solid Waste Management'), body_style)],
            [Paragraph("<b>Assigned Officer:</b>", body_style), Paragraph(complaint.get('assigned_officer', 'Zone Field Inspector'), body_style)],
            [Paragraph("<b>Officer Inspection Notes:</b>", body_style), Paragraph(complaint.get('inspection_notes') or "<i>Inspection awaiting site visit.</i>", body_style)],
            [Paragraph("<b>Remediation Action Taken:</b>", body_style), Paragraph(complaint.get('action_taken_notes') or "<i>Action pending verification.</i>", body_style)],
        ]
        officer_table = Table(officer_data, colWidths=[1.8 * inch, 5.2 * inch])
        officer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(officer_table)
        story.append(Spacer(1, 10))

        # Audit Trail Section
        story.append(Paragraph("Chronological Audit & Escalation Log", section_heading))
        audit_headers = [Paragraph("<b>Timestamp</b>", body_style), Paragraph("<b>Action Taken</b>", body_style), Paragraph("<b>Actor</b>", body_style), Paragraph("<b>Details</b>", body_style)]
        audit_rows = [audit_headers]
        for log in audit_trail:
            audit_rows.append([
                Paragraph(str(log.get('timestamp', '')), body_style),
                Paragraph(str(log.get('action', '')), body_style),
                Paragraph(str(log.get('performed_by', '')), body_style),
                Paragraph(str(log.get('details', '')), body_style),
            ])
        
        audit_table = Table(audit_rows, colWidths=[1.5 * inch, 1.8 * inch, 1.5 * inch, 2.2 * inch])
        audit_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#065f46")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(audit_table)
        story.append(Spacer(1, 15))

        # Sign-off Block
        sign_data = [
            [Paragraph("____________________________<br/><b>Inspecting Field Officer</b>", body_style),
             Paragraph("____________________________<br/><b>Zonal Sanitation Commissioner</b>", body_style),
             Paragraph("____________________________<br/><b>Department Official Stamp</b>", body_style)]
        ]
        sign_table = Table(sign_data, colWidths=[2.3 * inch, 2.4 * inch, 2.3 * inch])
        sign_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(KeepTogether(sign_table))

        # Build PDF
        doc.build(story)
        return str(pdf_path)

    except Exception as e:
        # Fallback to HTML printable report
        html_filename = f"Report_{complaint_id}.html"
        html_path = REPORTS_DIR / html_filename
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>ECOGUARD AI Report - {complaint_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 30px; color: #1e293b; }}
        .header {{ border-bottom: 3px solid #059669; padding-bottom: 12px; margin-bottom: 20px; }}
        .badge {{ background: #ecfdf5; color: #065f46; padding: 4px 10px; border-radius: 4px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; font-size: 14px; text-align: left; }}
        th {{ background: #f8fafc; font-weight: 600; }}
        .notice {{ background: #fef2f2; border-left: 4px solid #dc2626; padding: 10px; font-size: 13px; color: #991b1b; margin-bottom: 20px; }}
    </style>
</head>
<body onload="window.print()">
    <div class="header">
        <h2 style="color:#065f46; margin:0;">ECOGUARD AI – Environmental Incident & Audit Report</h2>
        <p style="margin:4px 0; color:#64748b;">Report ID: <strong>{complaint_id}</strong> | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="notice">
        <strong>LEGAL DISCLAIMER:</strong> AI image analysis observations are preliminary. Official enforcement mandates physical inspection by authorized municipal personnel.
    </div>
    <h3>Complaint & Location Details</h3>
    <table>
        <tr><th>Status</th><td><span class="badge">{complaint.get('status')}</span></td><th>Severity</th><td>{complaint.get('severity')}</td></tr>
        <tr><th>Reporter</th><td>{complaint.get('reporter_type')} ({complaint.get('reporter_name')})</td><th>Date</th><td>{complaint.get('created_at')}</td></tr>
        <tr><th>Coordinates</th><td>{complaint.get('latitude')}, {complaint.get('longitude')}</td><th>Escalation</th><td>Level {complaint.get('escalation_level')}</td></tr>
        <tr><th>Address</th><td colspan="3">{complaint.get('location_address')}</td></tr>
    </table>
    <h3>AI Environmental Observations</h3>
    <table>
        <tr><th>Primary Category</th><td><strong>{complaint.get('primary_category')}</strong></td></tr>
        <tr><th>Risk Assessment</th><td>{complaint.get('risk_assessment')}</td></tr>
        <tr><th>Impact</th><td>{complaint.get('environmental_impact')}</td></tr>
        <tr><th>Recommended Action</th><td>{complaint.get('recommended_action')}</td></tr>
    </table>
    <h3>Administrative Notes</h3>
    <table>
        <tr><th>Assigned Officer</th><td>{complaint.get('assigned_officer')} ({complaint.get('assigned_department')})</td></tr>
        <tr><th>Inspection Notes</th><td>{complaint.get('inspection_notes') or 'Pending inspection'}</td></tr>
        <tr><th>Action Taken</th><td>{complaint.get('action_taken_notes') or 'Pending verification'}</td></tr>
    </table>
</body>
</html>""")
        return str(html_path)
