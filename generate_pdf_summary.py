"""
Generate a 2-page PDF summary from the email analytics report v3.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import re
from datetime import datetime

INPUT_FILE = "email_analytics_report_v3.txt"
OUTPUT_FILE = "email_analytics_summary_v3.pdf"


def parse_report(filepath):
    """Parse the text report and extract key data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {}
    
    # Extract generated date
    match = re.search(r'Generated: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    data['generated'] = match.group(1) if match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract user counts
    match = re.search(r'Total Registered Users: (\d+)', content)
    data['total_users'] = int(match.group(1)) if match else 0
    
    match = re.search(r'Active Users: (\d+) \((\d+\.\d+)%\)', content)
    data['active_users'] = int(match.group(1)) if match else 0
    data['active_pct'] = match.group(2) if match else '0'
    
    match = re.search(r'Inactive Users: (\d+) \((\d+\.\d+)%\)', content)
    data['inactive_users'] = int(match.group(1)) if match else 0
    data['inactive_pct'] = match.group(2) if match else '0'
    
    # Extract event summary
    match = re.search(r'Total Events: ([\d,]+)', content)
    data['total_events'] = match.group(1) if match else '0'
    
    # Extract event types
    event_types = []
    event_pattern = r'-\s+([\w_]+)\s+:\s+([\d,]+)\s+\((\d+\.\d+)%\)'
    for m in re.finditer(event_pattern, content):
        event_types.append({
            'type': m.group(1).capitalize(),
            'count': m.group(2),
            'pct': m.group(3)
        })
    data['event_types'] = event_types[:9]  # Top 9 event types
    
    # Extract date range
    match = re.search(r'Date Range: (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', content)
    data['date_from'] = match.group(1) if match else 'N/A'
    data['date_to'] = match.group(2) if match else 'N/A'
    
    match = re.search(r'Total Days with Activity: (\d+)', content)
    data['active_days'] = match.group(1) if match else '0'
    
    match = re.search(r'Unique Senders in Events: (\d+)', content)
    data['unique_senders'] = match.group(1) if match else '0'
    
    # Extract top senders from Section 2B
    top_senders = []
    sender_section = re.search(r'SECTION 2B.*?SECTION 3', content, re.DOTALL)
    if sender_section:
        sender_pattern = r'(\S+@\S+)\s+\|\s+(Yes|No)\s+\|\s+([\d,]+)\s+\|\s+(\d+)\s+\|\s+([\d.]+)\s+\|\s+([\d]+)'
        for m in re.finditer(sender_pattern, sender_section.group()):
            top_senders.append({
                'email': m.group(1),
                'registered': m.group(2),
                'total_sent': m.group(3),
                'active_days': m.group(4),
                'avg_day': m.group(5),
                'max_day': m.group(6)
            })
    data['top_senders'] = top_senders[:6]  # Top 6
    
    # Extract user email volume from Section 3
    user_volume = []
    volume_section = re.search(r'User Email Volume Summary.*?Users with Email Activity', content, re.DOTALL)
    if volume_section:
        # Match: Name | status | sent | delivered | rate% | days | avg | max
        volume_pattern = r'^([A-Za-z][A-Za-z\s]+?)\s+\|\s+(active|inactive)\s+\|\s+([\d,]+)\s+\|\s+([\d,]+)\s+\|\s+(\d+\.\d+)%'
        for m in re.finditer(volume_pattern, volume_section.group(), re.MULTILINE):
            if int(m.group(3).replace(',', '')) > 0:
                user_volume.append({
                    'name': m.group(1).strip(),
                    'status': m.group(2),
                    'sent': m.group(3),
                    'delivered': m.group(4),
                    'rate': m.group(5)
                })
    data['user_volume'] = user_volume[:9]
    
    # Extract overall performance
    match = re.search(r'Total Emails Sent \(all users\): ([\d,]+)', content)
    data['total_sent'] = match.group(1) if match else '0'
    
    match = re.search(r'Total Expected.*?: ([\d,]+)', content)
    data['total_expected'] = match.group(1) if match else '0'
    
    match = re.search(r'Overall Achievement: ([\d.]+)%', content)
    data['overall_achievement'] = match.group(1) if match else '0'
    
    # Extract target achievement
    target_users = []
    target_section = re.search(r'Per-User Daily Target Achievement.*?Days Meeting Target', content, re.DOTALL)
    if target_section:
        target_pattern = r'([\w\s]+?)\s+\|\s+([\d.]+)\s+\|\s+\d+\s+\|\s+([\d.]+)%\s+\|\s+(\w+[\s\w]*)'
        for m in re.finditer(target_pattern, target_section.group()):
            if float(m.group(2)) > 0:
                target_users.append({
                    'name': m.group(1).strip(),
                    'avg_day': m.group(2),
                    'achievement': m.group(3),
                    'status': m.group(4).strip()
                })
    data['target_users'] = target_users[:9]
    
    # Extract top performers
    top_volume = []
    volume_match = re.search(r'Top 5 by Total Email Volume.*?Top 5 by Daily', content, re.DOTALL)
    if volume_match:
        for m in re.finditer(r'\d+\.\s+([\w\s]+?)\s+\|\s+([\d,]+)\s+emails', volume_match.group()):
            top_volume.append({'name': m.group(1).strip(), 'value': m.group(2)})
    data['top_volume'] = top_volume[:5]
    
    top_daily = []
    daily_match = re.search(r'Top 5 by Daily Average.*?Top 5 by Max', content, re.DOTALL)
    if daily_match:
        for m in re.finditer(r'\d+\.\s+([\w\s]+?)\s+\|\s+([\d.]+)\s+emails/day', daily_match.group()):
            top_daily.append({'name': m.group(1).strip(), 'value': m.group(2)})
    data['top_daily'] = top_daily[:5]
    
    top_delivery = []
    delivery_match = re.search(r'Top 5 by Delivery Rate.*?END OF REPORT', content, re.DOTALL)
    if delivery_match:
        for m in re.finditer(r'\d+\.\s+([\w\s]+?)\s+\|\s+([\d.]+)%', delivery_match.group()):
            top_delivery.append({'name': m.group(1).strip(), 'value': m.group(2)})
    data['top_delivery'] = top_delivery[:5]
    
    # Count users meeting target
    match = re.search(r'Users with Email Activity: (\d+)', content)
    data['users_with_activity'] = match.group(1) if match else '0'
    
    match = re.search(r'Users with No Email Activity: (\d+)', content)
    data['users_no_activity'] = match.group(1) if match else '0'
    
    # Extract weekly email frequency (daily breakdown per user)
    weekly_freq = []
    section4 = re.search(r'SECTION 4: DAILY EMAIL FREQUENCY.*?SECTION 5', content, re.DOTALL)
    if section4:
        # Parse each user's daily data
        user_blocks = re.finditer(r'>>> ([\w\s]+?)\s+\(([^)]+)\).*?Active Days: (\d+).*?(?=>>>|SECTION 5)', section4.group(), re.DOTALL)
        for user_match in user_blocks:
            user_name = user_match.group(1).strip()
            user_email = user_match.group(2).strip()
            daily_data = {}
            
            # Extract daily sends
            date_pattern = r'(\d{4}-\d{2}-\d{2})\s+\|\s+(\d+)\s+\|'
            for date_match in re.finditer(date_pattern, user_match.group()):
                date = date_match.group(1)
                sent = date_match.group(2)
                daily_data[date] = sent
            
            if daily_data:  # Only include users with data
                weekly_freq.append({
                    'name': user_name,
                    'email': user_email,
                    'daily': daily_data
                })
    data['weekly_freq'] = weekly_freq[:9]  # Top 9 users with activity
    
    return data


def create_pdf(data, output_path):
    """Generate the 2-page PDF summary."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor('#1a5276')
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor('#566573')
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#2874a6')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4
    )
    
    elements = []
    
    # ===== PAGE 1 =====
    
    # Title
    elements.append(Paragraph("MAILCHIMP EMAIL ANALYTICS SUMMARY", title_style))
    elements.append(Paragraph(f"Report Period: {data['date_from']} to {data['date_to']} | Generated: {data['generated']}", subtitle_style))
    elements.append(Spacer(1, 6))
    
    # Key Metrics Row
    elements.append(Paragraph("KEY METRICS", section_style))
    
    metrics_data = [
        ['Total Events', 'Active Days', 'Unique Senders', 'Overall Achievement'],
        [data['total_events'], data['active_days'], data['unique_senders'], f"{data['overall_achievement']}%"]
    ]
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2874a6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#eaf2f8')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2874a6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 10))
    
    # User Status and Event Types side by side
    elements.append(Paragraph("USER STATUS & EVENT DISTRIBUTION", section_style))
    
    # User Status Table
    user_status_data = [
        ['User Status', 'Count', '%'],
        ['Total Registered', str(data['total_users']), '100%'],
        ['Active Users', str(data['active_users']), f"{data['active_pct']}%"],
        ['Inactive Users', str(data['inactive_users']), f"{data['inactive_pct']}%"],
        ['Users with Activity', data['users_with_activity'], '-'],
        ['Users No Activity', data['users_no_activity'], '-'],
    ]
    
    # Event Types Table (include up to 7 to cover hard_bounce)
    event_data = [['Event Type', 'Count', '%']]
    for evt in data['event_types'][:7]:
        event_data.append([evt['type'], evt['count'], f"{evt['pct']}%"])
    
    # Create side-by-side tables
    user_table = Table(user_status_data, colWidths=[1.5*inch, 0.8*inch, 0.7*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d5dbdb')),
    ]))
    
    event_table = Table(event_data, colWidths=[1.2*inch, 0.9*inch, 0.7*inch])
    event_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
    ]))
    
    combined_table = Table([[user_table, event_table]], colWidths=[3.2*inch, 3*inch])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(combined_table)
    elements.append(Spacer(1, 10))
    
    # Top Senders Activity
    elements.append(Paragraph("TOP SENDERS ACTIVITY", section_style))
    
    sender_data = [['Sender Email', 'Reg?', 'Total Sent', 'Days', 'Avg/Day', 'Max/Day']]
    for s in data['top_senders']:
        sender_data.append([
            s['email'][:35] + '...' if len(s['email']) > 35 else s['email'],
            s['registered'],
            s['total_sent'],
            s['active_days'],
            s['avg_day'],
            s['max_day']
        ])
    
    sender_table = Table(sender_data, colWidths=[2.5*inch, 0.5*inch, 0.9*inch, 0.5*inch, 0.8*inch, 0.8*inch])
    sender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f7')]),
    ]))
    elements.append(sender_table)
    elements.append(Spacer(1, 10))
    
    # Weekly Email Activity Pattern
    elements.append(Paragraph("WEEKLY EMAIL ACTIVITY PATTERN (Daily Breakdown)", section_style))
    
    if data['weekly_freq']:
        # Get all unique dates from the data
        all_dates = set()
        for user in data['weekly_freq']:
            all_dates.update(user['daily'].keys())
        sorted_dates = sorted(list(all_dates))
        
        # Build table header with dates (show only last 5 chars for space: MM-DD)
        freq_header = ['User Name'] + [d[-5:] for d in sorted_dates[:7]]  # Limit to 7 days
        freq_data = [freq_header]
        
        for user in data['weekly_freq'][:6]:  # Top 6 users
            row = [user['name'][:20]]  # Truncate name
            for date in sorted_dates[:7]:
                row.append(user['daily'].get(date, '-'))
            freq_data.append(row)
        
        # Dynamic column widths
        col_count = len(freq_header)
        name_width = 1.8 * inch
        date_width = (7.2 * inch - name_width) / (col_count - 1) if col_count > 1 else 0.7*inch
        col_widths = [name_width] + [date_width] * (col_count - 1)
        
        freq_table = Table(freq_data, colWidths=col_widths)
        freq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f7')]),
        ]))
        elements.append(freq_table)
    
    # Page break
    elements.append(PageBreak())
    
    # ===== PAGE 2 =====
    
    # User Email Volume Summary (moved from page 1)
    elements.append(Paragraph("USER EMAIL VOLUME (Active Senders)", section_style))
    
    volume_data = [['User Name', 'Status', 'Sent', 'Delivered', 'Del. Rate']]
    for u in data['user_volume']:
        volume_data.append([u['name'], u['status'].upper(), u['sent'], u['delivered'], f"{u['rate']}%"])
    
    volume_table = Table(volume_data, colWidths=[2*inch, 0.8*inch, 1*inch, 1*inch, 0.9*inch])
    volume_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f7')]),
    ]))
    elements.append(volume_table)
    elements.append(Spacer(1, 12))
    
    # Performance Analysis as sub-heading
    elements.append(Paragraph("PERFORMANCE ANALYSIS", section_style))
    elements.append(Spacer(1, 6))
    
    # Target Achievement Summary
    elements.append(Paragraph("TARGET ACHIEVEMENT SUMMARY", section_style))
    
    target_summary = [
        ['Metric', 'Value'],
        ['Total Emails Sent', data['total_sent']],
        ['Total Expected (at 100%)', data['total_expected']],
        ['Overall Achievement', f"{data['overall_achievement']}%"],
    ]
    
    target_summary_table = Table(target_summary, colWidths=[2.5*inch, 2*inch])
    target_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2874a6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aed6f1')),
    ]))
    elements.append(target_summary_table)
    elements.append(Spacer(1, 15))
    
    # Key Observations
    elements.append(Paragraph("KEY OBSERVATIONS", section_style))
    
    observations = [
        f"• <b>User Engagement:</b> Only {data['users_with_activity']} out of {data['total_users']} registered users ({int(int(data['users_with_activity'])/int(data['total_users'])*100)}%) showed email activity during this period.",
        f"• <b>Target Achievement:</b> Overall target achievement is {data['overall_achievement']}%, indicating the team is performing below the 500 emails/user/day target.",
        f"• <b>Top Performer:</b> {data['top_volume'][0]['name'] if data['top_volume'] else 'N/A'} leads with {data['top_volume'][0]['value'] if data['top_volume'] else '0'} total emails sent.",
        f"• <b>Delivery Rate:</b> Top performers maintain 96-100% delivery rates, indicating good email hygiene.",
        f"• <b>Active Days:</b> The report covers {data['active_days']} days of activity from {data['date_from']} to {data['date_to']}.",
    ]
    
    for obs in observations:
        elements.append(Paragraph(obs, normal_style))
    
    elements.append(Spacer(1, 15))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#808080')
    )
    elements.append(Paragraph("— End of Summary Report —", footer_style))
    
    # Build PDF
    doc.build(elements)
    print(f"PDF generated successfully: {output_path}")


def main():
    print("Parsing report...")
    data = parse_report(INPUT_FILE)
    
    print("Generating PDF summary...")
    create_pdf(data, OUTPUT_FILE)
    
    print("Done!")


if __name__ == "__main__":
    main()
