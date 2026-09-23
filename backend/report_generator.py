import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

from detection_store import store

def generate_pdf_report(output_filename: str):
    doc = SimpleDocTemplate(output_filename, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    h2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # Header
    elements.append(Paragraph("OCEANATLAS", title_style))
    elements.append(Paragraph("SEAFLOOR METAL DETECTION REPORT", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    now_str = datetime.now().strftime("%d %B %Y, %H:%M")
    elements.append(Paragraph(f"<b>Report Generated:</b> {now_str}", normal_style))
    elements.append(Spacer(1, 0.4 * inch))
    
    # Summary Section
    elements.append(Paragraph("Detection Summary", h2_style))
    
    summary = store.get_summary()
    counts = summary["classes"]
    
    table_data = [["Detection Type", "Count"]]
    for cls_name, count in counts.items():
        table_data.append([cls_name, str(count)])
    table_data.append(["TOTAL", str(summary["total_detections"])])
    
    t = Table(table_data, colWidths=[3 * inch, 1 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Evidence Section
    elements.append(PageBreak())
    elements.append(Paragraph("DETECTION EVIDENCE", h2_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    history = store.get_history()
    
    if not history:
        elements.append(Paragraph("No detection evidence recorded for this session.", normal_style))
    else:
        for idx, det in enumerate(reversed(history)): # Chronological order
            elements.append(Paragraph(f"<b>Detection #{idx+1:03d}</b>", h2_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            elements.append(Paragraph(f"<b>Class:</b> {det['class_name']}", normal_style))
            elements.append(Paragraph(f"<b>Confidence:</b> {det['confidence']}%", normal_style))
            elements.append(Paragraph(f"<b>Timestamp:</b> {det['timestamp']}", normal_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            img_path = os.path.join(store.evidence_dir, det['image_filename'])
            if os.path.exists(img_path):
                # Resize proportionally to fit width
                img = Image(img_path)
                # target width = 5 inches
                target_width = 5 * inch
                ratio = target_width / img.drawWidth
                img.drawWidth = target_width
                img.drawHeight = img.drawHeight * ratio
                elements.append(img)
            else:
                elements.append(Paragraph("<i>[Image File Missing]</i>", normal_style))
                
            elements.append(Spacer(1, 0.4 * inch))
            
    doc.build(elements)
    return output_filename
