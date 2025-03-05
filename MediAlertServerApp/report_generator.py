from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        
    def generate_adverse_effects_report(self, data, filters=None):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Lista de elementos del PDF
        elements = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Reporte de Efectos Adversos", title_style))
        
        # Información del reporte
        elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles["Normal"]))
        if filters:
            elements.append(Paragraph(f"Filtros aplicados: {filters}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))
        
        # Estadísticas generales
        elements.append(Paragraph("Estadísticas Generales", self.styles["Heading2"]))
        stats_data = [
            ["Total de reportes", str(data['total_reports'])],
            ["Casos graves", str(data['severe_cases'])],
            ["Casos pendientes", str(data['pending_cases'])]
        ]
        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Detalles de los efectos adversos
        elements.append(Paragraph("Detalles de Efectos Adversos", self.styles["Heading2"]))
        detail_data = [['Medicamento', 'Severidad', 'Tipo', 'Fecha']]
        for effect in data['effects']:
            detail_data.append([
                effect['medication'],
                effect['severity'],
                effect['type'],
                effect['reported_at']
            ])
        detail_table = Table(detail_data)
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(detail_table)
        
        # Construir el PDF
        doc.build(elements)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf
