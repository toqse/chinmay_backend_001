from django.shortcuts import render
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image, Paragraph
from io import BytesIO
from houses.models import House, VisitHistory
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from dateutil.relativedelta import relativedelta

# Create your views here.

class GenerateReportView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get filter parameters
            panchayath_id = request.query_params.get('panchayath')
            ward_number = request.query_params.get('ward_number')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            # Convert string dates to datetime objects
            from_date = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
            to_date = datetime.strptime(to_date, '%Y-%m-%d') if to_date else None

            # Filter houses
            houses = House.objects.all()
            if panchayath_id:
                houses = houses.filter(panchayath_id=panchayath_id)
            if ward_number:
                houses = houses.filter(ward_number=ward_number)

            # Get panchayath name safely
            panchayath_name = "All"
            if panchayath_id:
                panchayath = houses.filter(panchayath_id=panchayath_id).first()
                if panchayath and panchayath.panchayath:
                    panchayath_name = panchayath.panchayath.username

            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            
            # Create title with date range
            title = f"House Visit Report - {panchayath_name}"
            if from_date and to_date:
                title += f" ({from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')})"
            elif from_date:
                title += f" (From {from_date.strftime('%Y-%m-%d')})"
            elif to_date:
                title += f" (Until {to_date.strftime('%Y-%m-%d')})"
            
            doc.title = title  # Add metadata title with date range
            elements = []

            # Add title and header information
            title_data = [
                ['House Visit Report'],
                [''],  # Empty row for spacing
                [f'Date Range: {from_date.strftime("%Y-%m-%d") if from_date else "All"} - {to_date.strftime("%Y-%m-%d") if to_date else "All"}'],
                [f'Panchayath: {panchayath_name}'],
            ]

            # Add product information if available
            if panchayath_id and panchayath and panchayath.panchayath:
                product_info = []
                if panchayath.panchayath.product_number:
                    product_info.append(panchayath.panchayath.product_number)
                if panchayath.panchayath.product_name:
                    product_info.append(panchayath.panchayath.product_name)
                if product_info:
                    title_data.append([f'Product Info: {", ".join(product_info)}'])

            title_table = Table(title_data)
            title_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 20),
                ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 2), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ]))
            elements.append(title_table)
            elements.append(Spacer(1, 30))

            # Group houses by ward
            wards = houses.values_list('ward_number', flat=True).distinct().order_by('ward_number')
            
            for ward in wards:
                # Ward header with modern styling
                ward_header = [[f'Ward {ward}']]
                ward_table = Table(ward_header, colWidths=[doc.width])
                ward_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 16),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Changed alignment to CENTER
                    ('PADDING', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ]))
                elements.append(ward_table)
                elements.append(Spacer(1, 20))

                ward_houses = houses.filter(ward_number=ward)
                
                for idx, house in enumerate(ward_houses, 1):
                    # House header
                    house_header = [[f'House {idx}: {house.house_number}']]
                    house_header_table = Table(house_header, colWidths=[doc.width])
                    house_header_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#424242')),
                        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),  # Changed alignment to LEFT
                        ('PADDING', (0, 0), (-1, 0), 8),
                    ]))
                    elements.append(house_header_table)
                    
                    # House details
                    house_info = [
                        ['Resident Name:', house.resident_name or 'Not provided'],
                        ['Mobile:', house.mobile_number],
                        ['Address:', house.address],
                        ['Total Visits:', str(house.visits.filter(
                            visit_date__gte=from_date,
                            visit_date__lte=to_date
                        ).count() if from_date and to_date else house.visits.count())]
                    ]

                    # Create a new table for house info with image on the right
                    house_info_table = Table(house_info, colWidths=[doc.width * 0.2, doc.width * 0.6])
                    house_info_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('PADDING', (0, 0), (-1, -1), 6),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    # Add photo if available
                    if house.photo:
                        try:
                            img = Image(house.photo.path, width=100, height=100)
                            # Create a new table to hold the image and house info side by side
                            combined_table = Table([[house_info_table, img]], colWidths=[doc.width * 0.5, doc.width * 0.4])
                            combined_table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                            ]))
                            elements.append(combined_table)
                        except Exception:
                            elements.append(house_info_table)
                            elements.append(Paragraph("Image not available", ParagraphStyle(
                                name='ImageNotAvailable',
                                fontName='Helvetica',
                                fontSize=10,
                                textColor=colors.gray,
                                alignment=1
                            )))
                    else:
                        elements.append(house_info_table)
                        elements.append(Paragraph("Image not available", ParagraphStyle(
                            name='ImageNotAvailable',
                            fontName='Helvetica',
                            fontSize=10,
                            textColor=colors.gray,
                            alignment=1
                        )))

                    elements.append(Spacer(1, 10))

                    # Visit details
                    visits = house.visits.filter(
                        visit_date__gte=from_date,
                        visit_date__lte=to_date
                    ) if from_date and to_date else house.visits.all()

                    if visits.exists():
                        visit_data = [['S.No', 'Visit Date', 'Coordinates', 'Review']]
                        for index, visit in enumerate(visits, 1):
                            visit_data.append([
                                str(index),
                                visit.visit_date.strftime('%Y-%m-%d'),
                                f'{visit.latitude}, {visit.longitude}',
                                visit.review or 'No review'
                            ])
                            
                        visit_table = Table(visit_data, colWidths=[
                            doc.width * 0.1,
                            doc.width * 0.2,
                            doc.width * 0.3,
                            doc.width * 0.4
                        ])
                        visit_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#212121')),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 10),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                            ('PADDING', (0, 0), (-1, -1), 8),
                        ]))
                        elements.append(Spacer(1, 10))
                        elements.append(visit_table)

                    elements.append(Spacer(1, 20))

            doc.build(elements)

            # Return PDF
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            
            # Create filename with panchayath and dates
            filename = panchayath_name
            if from_date and to_date:
                filename += f" {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"
            elif from_date:
                filename += f" {from_date.strftime('%Y-%m-%d')}"
            
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            
            return response

        except Exception as e:
            return Response(
                {'error': f'Error generating report: {str(e)}'},
                status=500
            )

class GenerateSixMonthReportView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get panchayath filter parameter
            panchayath_id = request.query_params.get('panchayath')

            # Filter houses
            houses = House.objects.all()
            if panchayath_id:
                houses = houses.filter(panchayath_id=panchayath_id)

            # Get panchayath name safely
            panchayath_name = "All"
            if panchayath_id:
                panchayath = houses.filter(panchayath_id=panchayath_id).first()
                if panchayath and panchayath.panchayath:
                    panchayath_name = panchayath.panchayath.username

            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            
            title = f"Six Month House Visit Report - {panchayath_name}"
            doc.title = title
            elements = []

            # Add title
            title_data = [
                ['Six Month House Visit Report'],
                [''],  # Empty row for spacing
                [f'Panchayath: {panchayath_name}'],
            ]

            # Add product information if available
            if panchayath_id and panchayath and panchayath.panchayath:
                product_info = []
                if panchayath.panchayath.product_number:
                    product_info.append(panchayath.panchayath.product_number)
                if panchayath.panchayath.product_name:
                    product_info.append(panchayath.panchayath.product_name)
                if product_info:
                    title_data.append([f'Product Info: {", ".join(product_info)}'])

            title_table = Table(title_data)
            title_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 20),
                ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 2), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ]))
            elements.append(title_table)
            elements.append(Spacer(1, 30))

            # Group houses by ward
            wards = houses.values_list('ward_number', flat=True).distinct().order_by('ward_number')
            
            for ward in wards:
                ward_houses = houses.filter(ward_number=ward)
                
                # Ward header
                ward_header = [[f'Ward {ward}']]
                ward_table = Table(ward_header, colWidths=[doc.width])
                ward_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 16),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('PADDING', (0, 0), (-1, 0), 12),
                ]))
                elements.append(ward_table)
                elements.append(Spacer(1, 20))

                for idx, house in enumerate(ward_houses, 1):
                    # Get first visit date for this house
                    first_visit = house.visits.order_by('visit_date').first()
                    if not first_visit:
                        continue

                    start_date = first_visit.visit_date
                    end_date = start_date + relativedelta(months=6)

                    # Get visits within 6 months of first visit
                    visits = house.visits.filter(
                        visit_date__gte=start_date,
                        visit_date__lte=end_date
                    ).order_by('visit_date')

                    if not visits.exists():
                        continue

                    # House header with date range
                    house_header = [[f'House {idx}: {house.house_number} ({start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")})']]
                    house_header_table = Table(house_header, colWidths=[doc.width])
                    house_header_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#424242')),
                        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                        ('PADDING', (0, 0), (-1, 0), 8),
                    ]))
                    elements.append(house_header_table)

                    # House details and visit table (similar to original report)
                    house_info = [
                        ['Resident Name:', house.resident_name or 'Not provided'],
                        ['Mobile:', house.mobile_number],
                        ['Address:', house.address],
                        ['Total Visits:', str(visits.count())]
                    ]

                    house_info_table = Table(house_info, colWidths=[doc.width * 0.2, doc.width * 0.6])
                    house_info_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('PADDING', (0, 0), (-1, -1), 6),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    # Add photo if available
                    if house.photo:
                        try:
                            img = Image(house.photo.path, width=100, height=100)
                            # Create a new table to hold the image and house info side by side
                            combined_table = Table([[house_info_table, img]], colWidths=[doc.width * 0.5, doc.width * 0.4])
                            combined_table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                            ]))
                            elements.append(combined_table)
                        except Exception:
                            elements.append(house_info_table)
                            elements.append(Paragraph("Image not available", ParagraphStyle(
                                name='ImageNotAvailable',
                                fontName='Helvetica',
                                fontSize=10,
                                textColor=colors.gray,
                                alignment=1
                            )))
                    else:
                        elements.append(house_info_table)
                        elements.append(Paragraph("Image not available", ParagraphStyle(
                            name='ImageNotAvailable',
                            fontName='Helvetica',
                            fontSize=10,
                            textColor=colors.gray,
                            alignment=1
                        )))

                    elements.append(Spacer(1, 10))

                    # Visit details table
                    visit_data = [['S.No', 'Visit Date', 'Coordinates', 'Review']]
                    for visit_idx, visit in enumerate(visits, 1):
                        visit_data.append([
                            str(visit_idx),
                            visit.visit_date.strftime('%Y-%m-%d'),
                            f'{visit.latitude}, {visit.longitude}',
                            visit.review or 'No review'
                        ])
                        
                    visit_table = Table(visit_data, colWidths=[
                        doc.width * 0.1,
                        doc.width * 0.2,
                        doc.width * 0.3,
                        doc.width * 0.4
                    ])
                    visit_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#212121')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                        ('PADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(visit_table)
                    elements.append(Spacer(1, 20))

            doc.build(elements)

            # Return PDF
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Six_Month_Report_{panchayath_name}.pdf"'
            
            return response

        except Exception as e:
            return Response(
                {'error': f'Error generating report: {str(e)}'},
                status=500
            )
