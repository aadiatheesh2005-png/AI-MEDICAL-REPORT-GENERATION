from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image as RLImage, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
import datetime
import os

# Color palette
DARK_NAVY = colors.HexColor('#0a1628')
ROYAL_BLUE = colors.HexColor('#1a3a6b')
ACCENT_BLUE = colors.HexColor('#2563eb')
LIGHT_BLUE = colors.HexColor('#dbeafe')
SUCCESS = colors.HexColor('#059669')
WARNING = colors.HexColor('#d97706')
DANGER = colors.HexColor('#dc2626')
CRITICAL = colors.HexColor('#7c3aed')
LIGHT_GRAY = colors.HexColor('#f8fafc')
MID_GRAY = colors.HexColor('#e2e8f0')
TEXT_DARK = colors.HexColor('#1e293b')
TEXT_MID = colors.HexColor('#475569')
TEXT_LIGHT = colors.HexColor('#94a3b8')
WHITE = colors.white

def get_risk_color(risk):
    return {'Low': SUCCESS, 'Moderate': WARNING, 'High': DANGER, 'Critical': CRITICAL}.get(risk, ACCENT_BLUE)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        w, h = A4
        self.setFillColor(TEXT_LIGHT)
        self.setFont("Helvetica", 8)
        self.drawCentredString(w/2, 15*mm, f"Page {self._pageNumber} of {page_count}  |  MedAI Diagnostic Report  |  Confidential Medical Document")
        # Footer line
        self.setStrokeColor(MID_GRAY)
        self.setLineWidth(0.5)
        self.line(20*mm, 20*mm, w-20*mm, 20*mm)


def header_footer(canvas_obj, doc, report_id, patient_name):
    w, h = A4
    canvas_obj.saveState()

    # Top accent bar
    canvas_obj.setFillColor(DARK_NAVY)
    canvas_obj.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)

    # Header text
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(20*mm, h - 11*mm, "MedAI DIAGNOSTIC SYSTEM")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor('#93c5fd'))
    canvas_obj.drawString(20*mm, h - 15.5*mm, "AI-Powered Clinical Intelligence Platform  |  Random Forest Analysis Engine")

    # Right side header info
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 8)
    canvas_obj.drawRightString(w - 20*mm, h - 11*mm, f"Report ID: {report_id}")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor('#93c5fd'))
    canvas_obj.drawRightString(w - 20*mm, h - 15.5*mm, f"Patient: {patient_name}")

    canvas_obj.restoreState()


def generate_medical_pdf(patient_data, ai_result, image_analysis, image_path, output_path, report_id):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )

    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=18, textColor=DARK_NAVY,
                                  spaceAfter=4, alignment=TA_LEFT)
    subtitle_style = ParagraphStyle('Sub', fontName='Helvetica', fontSize=10, textColor=TEXT_MID,
                                     spaceAfter=12, alignment=TA_LEFT)
    section_header = ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE,
                                     backColor=ROYAL_BLUE, spaceBefore=12, spaceAfter=6,
                                     leftIndent=-5, rightIndent=-5, leading=20)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
                                 spaceAfter=4, leading=14, alignment=TA_JUSTIFY)
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=TEXT_MID)
    value_style = ParagraphStyle('Value', fontName='Helvetica-Bold', fontSize=10, textColor=TEXT_DARK)
    small_style = ParagraphStyle('Small', fontName='Helvetica', fontSize=8, textColor=TEXT_MID, leading=12)
    finding_style = ParagraphStyle('Finding', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
                                    leftIndent=10, spaceAfter=3, leading=13)
    rec_style = ParagraphStyle('Rec', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
                                leftIndent=15, spaceAfter=4, leading=13, bulletIndent=5)

    # ── HEADER SECTION ──────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("MEDICAL DIAGNOSTIC REPORT", title_style))
    story.append(Paragraph(f"Generated: {patient_data['report_date']} at {patient_data['report_time']}  |  Algorithm: {ai_result.get('algorithm', 'Random Forest')}  |  Model Accuracy: {ai_result.get('model_accuracy', '94.7%')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceAfter=10))

    # ── PATIENT INFORMATION ──────────────────────────────────────────
    story.append(Paragraph("  PATIENT INFORMATION", section_header))
    story.append(Spacer(1, 2*mm))

    bmi = patient_data.get('weight', 70) / ((patient_data.get('height', 170)/100)**2)
    pat_data = [
        [Paragraph('<b>Full Name</b>', label_style), Paragraph(patient_data['name'], value_style),
         Paragraph('<b>Report ID</b>', label_style), Paragraph(report_id, value_style)],
        [Paragraph('<b>Age</b>', label_style), Paragraph(f"{patient_data['age']} years", value_style),
         Paragraph('<b>Gender</b>', label_style), Paragraph(patient_data['gender'], value_style)],
        [Paragraph('<b>Weight / Height</b>', label_style), Paragraph(f"{patient_data['weight']} kg / {patient_data['height']} cm", value_style),
         Paragraph('<b>BMI</b>', label_style), Paragraph(f"{bmi:.1f} kg/m²", value_style)],
        [Paragraph('<b>Attending Physician</b>', label_style), Paragraph(patient_data['doctor_name'], value_style),
         Paragraph('<b>Contact</b>', label_style), Paragraph(patient_data['doctor_email'], value_style)],
    ]
    pat_table = Table(pat_data, colWidths=[38*mm, 52*mm, 38*mm, 52*mm])
    pat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GRAY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(pat_table)

    # ── AI RISK ASSESSMENT BANNER ────────────────────────────────────
    story.append(Spacer(1, 5*mm))
    risk = ai_result.get('risk_level', 'Low')
    risk_color = get_risk_color(risk)

    risk_data = [
        [Paragraph(f'<b>AI RISK ASSESSMENT</b>', ParagraphStyle('rh', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_MID)),
         Paragraph(f'<b>CONFIDENCE SCORE</b>', ParagraphStyle('rh', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_MID)),
         Paragraph(f'<b>PRIMARY DIAGNOSIS</b>', ParagraphStyle('rh', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_MID))],
        [Paragraph(f'<b>{risk} RISK</b>',
                   ParagraphStyle('rv', fontName='Helvetica-Bold', fontSize=22, textColor=risk_color)),
         Paragraph(f'<b>{ai_result.get("confidence", 0)}%</b>',
                   ParagraphStyle('rv2', fontName='Helvetica-Bold', fontSize=22, textColor=ACCENT_BLUE)),
         Paragraph(ai_result.get('primary_diagnosis', 'N/A'),
                   ParagraphStyle('rv3', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK, leading=13))],
    ]
    risk_table = Table(risk_data, colWidths=[55*mm, 45*mm, 80*mm])
    risk_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, risk_color),
        ('LINEAFTER', (0,0), (0,-1), 0.5, MID_GRAY),
        ('LINEAFTER', (1,0), (1,-1), 0.5, MID_GRAY),
        ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(risk_table)

    # ── VITALS ──────────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("  VITAL SIGNS ANALYSIS", section_header))
    story.append(Spacer(1, 2*mm))

    vitals = ai_result.get('vitals_status', {})
    vitals_rows = [
        [Paragraph('<b>Parameter</b>', label_style), Paragraph('<b>Value</b>', label_style),
         Paragraph('<b>Status</b>', label_style), Paragraph('<b>Reference Range</b>', label_style)],
        ['Blood Pressure', patient_data.get('blood_pressure', 'N/A') + ' mmHg',
         vitals.get('blood_pressure', {}).get('status', 'N/A'), '90–140 / 60–90 mmHg'],
        ['Heart Rate', f"{patient_data.get('heart_rate', 'N/A')} bpm",
         vitals.get('heart_rate', {}).get('status', 'N/A'), '60–100 bpm'],
        ['Body Temperature', f"{patient_data.get('temperature', 'N/A')}°F",
         vitals.get('temperature', {}).get('status', 'N/A'), '97.0–99.0°F'],
        ['Oxygen Saturation', f"{patient_data.get('oxygen_saturation', 'N/A')}%",
         vitals.get('oxygen', {}).get('status', 'N/A'), '≥ 95%'],
        ['Blood Glucose', f"{patient_data.get('glucose', 'N/A')} mg/dL",
         vitals.get('glucose', {}).get('status', 'N/A'), '70–140 mg/dL'],
        ['Total Cholesterol', f"{patient_data.get('cholesterol', 'N/A')} mg/dL",
         vitals.get('cholesterol', {}).get('status', 'N/A'), '< 200 mg/dL'],
    ]

    def vital_row_style(rows):
        style = [
            ('BACKGROUND', (0,0), (-1,0), ROYAL_BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, MID_GRAY),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 7),
        ]
        for i, row in enumerate(rows[1:], 1):
            status = row[2]
            bg = colors.HexColor('#f0fdf4') if status == 'Normal' else colors.HexColor('#fef2f2')
            style.append(('BACKGROUND', (0,i), (-1,i), bg))
            tc = SUCCESS if status == 'Normal' else DANGER
            style.append(('TEXTCOLOR', (2,i), (2,i), tc))
            style.append(('FONTNAME', (2,i), (2,i), 'Helvetica-Bold'))
        return style

    vitals_table = Table(vitals_rows, colWidths=[45*mm, 40*mm, 30*mm, 65*mm])
    vitals_table.setStyle(TableStyle(vital_row_style(vitals_rows)))
    story.append(vitals_table)

    # ── CLINICAL FINDINGS ────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("  CLINICAL FINDINGS", section_header))
    story.append(Spacer(1, 2*mm))
    for finding in ai_result.get('findings', []):
        story.append(Paragraph(f"▸  {finding}", finding_style))

    # Secondary diagnoses
    sec_diags = ai_result.get('secondary_diagnoses', [])
    if sec_diags:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph('<b>Secondary / Differential Diagnoses:</b>', label_style))
        story.append(Spacer(1, 2*mm))
        for d in sec_diags:
            story.append(Paragraph(f"•  {d}", finding_style))

    # Symptoms & History
    if patient_data.get('symptoms'):
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph('<b>Reported Symptoms:</b>', label_style))
        story.append(Paragraph(patient_data['symptoms'], body_style))
    if patient_data.get('medical_history'):
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph('<b>Medical History:</b>', label_style))
        story.append(Paragraph(patient_data['medical_history'], body_style))
    if patient_data.get('medications'):
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph('<b>Current Medications:</b>', label_style))
        story.append(Paragraph(patient_data['medications'], body_style))
    if patient_data.get('allergies'):
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph('<b>Known Allergies:</b>', label_style))
        story.append(Paragraph(patient_data['allergies'], body_style))

    # ── AI FEATURE IMPORTANCE ────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("  AI MODEL — FEATURE IMPORTANCE (Random Forest)", section_header))
    story.append(Spacer(1, 3*mm))

    fi = ai_result.get('feature_importance', {})
    sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)

    fi_rows = [[Paragraph('<b>Clinical Parameter</b>', label_style),
                Paragraph('<b>Importance Score</b>', label_style),
                Paragraph('<b>Contribution Level</b>', label_style)]]
    for name, score in sorted_fi:
        bar_len = int(score * 2.5)
        bar = '█' * max(1, bar_len)
        level = 'High' if score > 15 else ('Medium' if score > 8 else 'Low')
        fi_rows.append([name, f"{score}%", f"{bar} {level}"])

    fi_table = Table(fi_rows, colWidths=[60*mm, 35*mm, 85*mm])
    fi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ROYAL_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('TEXTCOLOR', (2,1), (2,-1), ACCENT_BLUE),
    ]))
    story.append(fi_table)

    # ── RISK PROBABILITY DISTRIBUTION ───────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("  RISK PROBABILITY DISTRIBUTION", section_header))
    story.append(Spacer(1, 3*mm))

    prob_dist = ai_result.get('probability_distribution', {})
    prob_rows = [[Paragraph('<b>Risk Category</b>', label_style), Paragraph('<b>Probability</b>', label_style), Paragraph('<b>Visual</b>', label_style)]]
    risk_order = ['Low', 'Moderate', 'High', 'Critical']
    risk_clrs = [SUCCESS, WARNING, DANGER, CRITICAL]
    for r, rc in zip(risk_order, risk_clrs):
        prob = prob_dist.get(r, 0)
        bar = '█' * max(1, int(prob / 3))
        prob_rows.append([Paragraph(f'<b>{r}</b>', ParagraphStyle('pb', fontName='Helvetica-Bold', fontSize=9, textColor=rc)),
                          f"{prob}%", bar])

    prob_table = Table(prob_rows, colWidths=[50*mm, 40*mm, 90*mm])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ROYAL_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0,0), (-1,-1), 0.5, MID_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(prob_table)

    # ── IMAGE ANALYSIS ───────────────────────────────────────────────
    if image_analysis and image_analysis.get('analyzed'):
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("  MEDICAL IMAGE ANALYSIS", section_header))
        story.append(Spacer(1, 3*mm))

        img_content = []
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image as PILImage
                pil_img = PILImage.open(image_path)
                max_w, max_h = 60*mm, 50*mm
                aspect = pil_img.width / pil_img.height
                if aspect > 1:
                    img_w = max_w
                    img_h = max_w / aspect
                else:
                    img_h = max_h
                    img_w = max_h * aspect
                img_content.append(RLImage(image_path, width=img_w, height=img_h))
            except:
                pass

        img_info = [
            [Paragraph('<b>Dimensions</b>', label_style), image_analysis.get('dimensions', 'N/A')],
            [Paragraph('<b>Primary Finding</b>', label_style), image_analysis.get('finding', 'N/A')],
            [Paragraph('<b>Texture Analysis</b>', label_style), image_analysis.get('texture', 'N/A')],
            [Paragraph('<b>Concern Level</b>', label_style), image_analysis.get('concern_level', 'N/A')],
            [Paragraph('<b>RGB Analysis</b>', label_style), image_analysis.get('rgb_analysis', 'N/A')],
            [Paragraph('<b>AI Note</b>', label_style), Paragraph(image_analysis.get('note', ''), small_style)],
        ]
        info_table = Table(img_info, colWidths=[45*mm, 135*mm])
        info_table.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT_GRAY, WHITE]),
            ('GRID', (0,0), (-1,-1), 0.5, MID_GRAY),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))

        if img_content:
            outer = Table([[img_content[0], info_table]], colWidths=[68*mm, 112*mm])
            outer.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
            story.append(outer)
        else:
            story.append(info_table)

    # ── RECOMMENDATIONS ──────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("  CLINICAL RECOMMENDATIONS", section_header))
    story.append(Spacer(1, 3*mm))

    for i, rec in enumerate(ai_result.get('recommendations', []), 1):
        story.append(Paragraph(f"<b>{i}.</b>  {rec}", rec_style))

    # ── DISCLAIMER ───────────────────────────────────────────────────
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Spacer(1, 3*mm))

    disclaimer_box = Table([[Paragraph(
        '<b>IMPORTANT DISCLAIMER:</b> This report is generated by an AI-powered diagnostic support system using the Random Forest machine learning algorithm. '
        'The findings, diagnoses, and recommendations contained herein are intended to assist qualified healthcare professionals and do NOT '
        'constitute a definitive medical diagnosis. This report must be reviewed, interpreted, and validated by a licensed medical professional '
        'before any clinical decisions are made. The AI model has a reported accuracy of 94.7% on training data but may not reflect individual '
        'clinical circumstances. In case of emergency, contact emergency services immediately.',
        ParagraphStyle('disclaimer', fontName='Helvetica', fontSize=7.5, textColor=TEXT_MID, leading=11, alignment=TA_JUSTIFY)
    )]], colWidths=[170*mm])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff7ed')),
        ('BOX', (0,0), (-1,-1), 1, WARNING),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(disclaimer_box)

    story.append(Spacer(1, 4*mm))
    sig_data = [
        [Paragraph('<b>Physician Signature</b>', label_style), '', Paragraph('<b>Date & Time</b>', label_style)],
        [Paragraph('_' * 30, body_style), '', Paragraph(f"{patient_data['report_date']}, {patient_data['report_time']}", body_style)],
        [Paragraph(patient_data['doctor_name'], ParagraphStyle('sig', fontName='Helvetica-Bold', fontSize=9, textColor=ACCENT_BLUE)), '',
         Paragraph(f"Report ID: {report_id}", small_style)],
    ]
    sig_table = Table(sig_data, colWidths=[80*mm, 20*mm, 80*mm])
    sig_table.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(sig_table)

    # Build with header/footer
    def make_header(canvas_obj, doc):
        header_footer(canvas_obj, doc, report_id, patient_data['name'])

    doc.build(story, onFirstPage=make_header, onLaterPages=make_header, canvasmaker=NumberedCanvas)
