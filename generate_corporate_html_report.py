"""
Generate a production-quality corporate HTML report from email analytics data.
Minimal design, no external dependencies, corporate color palette.
"""

import re
from datetime import datetime

INPUT_FILE = "test/email_analytics_report_v3.txt"


def parse_report(filepath):
    """Parse the text report and extract key data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {}
    
    match = re.search(r'Generated: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    data['generated'] = match.group(1) if match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    match = re.search(r'Total Registered Users: (\d+)', content)
    data['total_users'] = int(match.group(1)) if match else 0
    
    match = re.search(r'Active Users: (\d+) \((\d+\.\d+)%\)', content)
    data['active_users'] = int(match.group(1)) if match else 0
    data['active_pct'] = match.group(2) if match else '0'
    
    match = re.search(r'Inactive Users: (\d+) \((\d+\.\d+)%\)', content)
    data['inactive_users'] = int(match.group(1)) if match else 0
    data['inactive_pct'] = match.group(2) if match else '0'
    
    match = re.search(r'Total Events: ([\d,]+)', content)
    data['total_events'] = match.group(1) if match else '0'
    
    event_types = []
    event_pattern = r'-\s+([\w_]+)\s+:\s+([\d,]+)\s+\((\d+\.\d+)%\)'
    for m in re.finditer(event_pattern, content):
        event_types.append({
            'type': m.group(1).capitalize().replace('_', ' '),
            'count': m.group(2),
            'pct': float(m.group(3))
        })
    data['event_types'] = event_types
    
    # Extract specific email metrics for calculations
    event_dict = {evt['type'].lower().replace(' ', '_'): int(evt['count'].replace(',', '')) for evt in event_types}
    
    # Map event names (case-insensitive lookup with common variations)
    sent = event_dict.get('send', 0) or event_dict.get('sent', 0)
    delivered = event_dict.get('delivered', 0)
    opened = event_dict.get('open', 0) or event_dict.get('opened', 0)
    hard_bounce = event_dict.get('hard_bounce', 0)
    soft_bounce = event_dict.get('soft_bounce', 0)
    unsubscribed = event_dict.get('unsub', 0) or event_dict.get('unsubscribed', 0)
    
    # Calculate rates with safe division
    delivery_rate = (delivered / sent * 100) if sent > 0 else 0.0
    not_delivered_rate = 100.0 - delivery_rate if sent > 0 else 0.0
    engagement_rate = (opened / delivered * 100) if delivered > 0 else 0.0
    not_engaged_rate = 100.0 - engagement_rate if delivered > 0 else 0.0
    failure_rate = ((hard_bounce + soft_bounce) / sent * 100) if sent > 0 else 0.0
    unsubscribe_rate = (unsubscribed / delivered * 100) if delivered > 0 else 0.0
    
    # Calculate percentages relative to sent for display in the card
    opened_pct_of_sent = (opened / sent * 100) if sent > 0 else 0.0
    unsubscribe_pct_of_sent = (unsubscribed / sent * 100) if sent > 0 else 0.0
    
    # Store email metrics
    data['email_metrics'] = {
        'sent': sent,
        'delivered': delivered,
        'delivery_rate': round(delivery_rate, 1),
        'not_delivered_rate': round(not_delivered_rate, 1),
        'opened': opened,
        'opened_pct_of_sent': round(opened_pct_of_sent, 1),
        'engagement_rate': round(engagement_rate, 1),
        'not_engaged_rate': round(not_engaged_rate, 1),
        'failures': hard_bounce + soft_bounce,
        'failure_rate': round(failure_rate, 1),
        'unsubscribed': unsubscribed,
        'unsubscribe_pct_of_sent': round(unsubscribe_pct_of_sent, 1),
        'unsubscribe_rate': round(unsubscribe_rate, 1)
    }
    
    match = re.search(r'Date Range: (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', content)
    data['date_from'] = match.group(1) if match else 'N/A'
    data['date_to'] = match.group(2) if match else 'N/A'
    
    match = re.search(r'Total Days with Activity: (\d+)', content)
    data['active_days'] = match.group(1) if match else '0'
    
    match = re.search(r'Unique Senders in Events: (\d+)', content)
    data['unique_senders'] = match.group(1) if match else '0'
    
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
    data['top_senders'] = top_senders[:10]
    
    user_volume = []
    volume_section = re.search(r'User Email Volume Summary.*?Users with Email Activity', content, re.DOTALL)
    if volume_section:
        volume_pattern = r'^([A-Za-z][A-Za-z\s]+?)\s+\|\s+(active|inactive)\s+\|\s+([\d,]+)\s+\|\s+([\d,]+)\s+\|\s+(\d+\.\d+)%'
        for m in re.finditer(volume_pattern, volume_section.group(), re.MULTILINE):
            if int(m.group(3).replace(',', '')) > 0:
                user_volume.append({
                    'name': m.group(1).strip(),
                    'status': m.group(2),
                    'sent': m.group(3),
                    'delivered': m.group(4),
                    'rate': float(m.group(5))
                })
    data['user_volume'] = user_volume
    
    match = re.search(r'Total Emails Sent \(all users\): ([\d,]+)', content)
    data['total_sent'] = match.group(1) if match else '0'
    
    match = re.search(r'Total Expected.*?: ([\d,]+)', content)
    data['total_expected'] = match.group(1) if match else '0'
    
    match = re.search(r'Overall Achievement: ([\d.]+)%', content)
    data['overall_achievement'] = float(match.group(1)) if match else 0.0
    
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
    
    match = re.search(r'Users with Email Activity: (\d+)', content)
    data['users_with_activity'] = match.group(1) if match else '0'
    
    match = re.search(r'Users with No Email Activity: (\d+)', content)
    data['users_no_activity'] = match.group(1) if match else '0'
    
    weekly_freq = []
    section4 = re.search(r'SECTION 4: DAILY EMAIL FREQUENCY.*?SECTION 5', content, re.DOTALL)
    if section4:
        user_blocks = re.finditer(r'>>> ([\w\s]+?)\s+\(([^)]+)\).*?Active Days: (\d+).*?(?=>>>|SECTION 5)', section4.group(), re.DOTALL)
        for user_match in user_blocks:
            user_name = user_match.group(1).strip()
            user_email = user_match.group(2).strip()
            daily_data = {}
            
            date_pattern = r'(\d{4}-\d{2}-\d{2})\s+\|\s+(\d+)\s+\|'
            for date_match in re.finditer(date_pattern, user_match.group()):
                date = date_match.group(1)
                sent = date_match.group(2)
                daily_data[date] = int(sent)
            
            if daily_data:
                weekly_freq.append({
                    'name': user_name,
                    'email': user_email,
                    'daily': daily_data
                })
    data['weekly_freq'] = weekly_freq
    
    return data


def generate_html(data, output_path):
    """Generate production-quality corporate HTML report."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Minder Email Analytics Report</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 10mm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            width: 100%;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #ffffff;
            color: #1a202c;
            font-size: 12px;
            line-height: 1.4;
            padding: 0;
        }}
        
        .container {{
            width: 100%;
            max-width: none;
            margin: 0;
            background-color: #ffffff;
            border-radius: 0;
            overflow: visible;
        }}
        
        .header {{
            background-color: #1e3a8a;
            color: #ffffff;
            padding: 24px 32px;
            border-bottom: 1px solid #1e40af;
        }}
        
        .header-title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.025em;
        }}
        
        .header-meta {{
            font-size: 11px;
            opacity: 0.9;
            font-weight: 400;
        }}
        
        .content {{
            padding: 24px 32px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        
        .metric-card {{
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 6px;
            padding: 16px;
        }}
        
        .metric-label {{
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #1e3a8a;
            line-height: 1;
            margin-bottom: 8px;
        }}
        
        .metric-subtext {{
            font-size: 10px;
            color: #64748b;
        }}
        
        .section {{
            margin-bottom: 32px;
        }}
        
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1e3a8a;
            margin-bottom: 8px;
        }}
        
        .section-divider {{
            height: 2px;
            background-color: #3b82f6;
            margin-bottom: 16px;
        }}
        
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }}
        
        .card {{
            background-color: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 6px;
            padding: 16px;
        }}
        
        .card-title {{
            font-size: 14px;
            font-weight: 600;
            color: #1e3a8a;
            margin-bottom: 16px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            table-layout: fixed;
            word-break: break-word;
        }}
        
        thead {{
            background-color: #f8fafc;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            display: table-header-group;
        }}
        
        th {{
            padding: 6px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            text-transform: uppercase;
            font-size: 9px;
            letter-spacing: 0.05em;
        }}
        
        th.numeric {{
            text-align: right;
        }}
        
        td {{
            padding: 6px;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        td.numeric {{
            text-align: right;
            font-variant-numeric: tabular-nums;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        
        tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        
        .badge-yes {{
            background-color: #dbeafe;
            color: #1e40af;
        }}
        
        .badge-no {{
            background-color: #f1f5f9;
            color: #64748b;
        }}
        
        .badge-active {{
            background-color: #dbeafe;
            color: #1e40af;
        }}
        
        .badge-inactive {{
            background-color: #f1f5f9;
            color: #64748b;
        }}
        
        .progress-bar {{
            height: 20px;
            background-color: #f1f5f9;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background-color: #3b82f6;
            display: flex;
            align-items: center;
            padding: 0 8px;
            color: #ffffff;
            font-size: 9px;
            font-weight: 600;
        }}
        
        .bar-chart-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .bar-label {{
            width: 120px;
            font-size: 11px;
            font-weight: 500;
            color: #334155;
        }}
        
        .bar-container {{
            flex: 1;
            display: flex;
            align-items: center;
        }}
        
        .bar {{
            height: 20px;
            background-color: #3b82f6;
            border-radius: 3px;
            margin-right: 8px;
        }}
        
        .bar-value {{
            font-size: 11px;
            color: #64748b;
            font-variant-numeric: tabular-nums;
            min-width: 100px;
        }}
        
        .heatmap-container {{
            overflow-x: visible;
        }}
        
        .heatmap-table {{
            min-width: auto;
        }}
        
        .heatmap-table td {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }}
        
        .heat-0 {{
            background-color: #f1f5f9;
            color: #94a3b8;
        }}
        
        .heat-1 {{
            background-color: #e0f2fe;
            color: #075985;
        }}
        
        .heat-2 {{
            background-color: #bae6fd;
            color: #075985;
        }}
        
        .heat-3 {{
            background-color: #7dd3fc;
            color: #0c4a6e;
        }}
        
        .heat-4 {{
            background-color: #38bdf8;
            color: #0c4a6e;
        }}
        
        .heat-5 {{
            background-color: #0ea5e9;
            color: #ffffff;
        }}
        
        .heat-6 {{
            background-color: #0284c7;
            color: #ffffff;
        }}
        
        .top-performers-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        
        .performer-card {{
            border: 1px solid #e2e8f0;
            border-left: 3px solid #3b82f6;
            padding: 12px;
            border-radius: 6px;
            background-color: #ffffff;
        }}
        
        .performer-rank {{
            font-size: 9px;
            text-transform: uppercase;
            color: #64748b;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}
        
        .performer-name {{
            font-size: 12px;
            font-weight: 600;
            color: #1e3a8a;
            margin-bottom: 3px;
        }}
        
        .performer-value {{
            font-size: 11px;
            color: #64748b;
            font-variant-numeric: tabular-nums;
        }}
        
        .observations-list {{
            list-style: none;
            padding: 0;
        }}
        
        .observations-list li {{
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .observations-list li:last-child {{
            border-bottom: none;
        }}
        
        .observation-title {{
            font-weight: 600;
            color: #1e3a8a;
            margin-bottom: 4px;
            font-size: 12px;
        }}
        
        .observation-text {{
            color: #475569;
            font-size: 11px;
        }}
        
        .footer {{
            background-color: #f8fafc;
            padding: 16px 32px;
            text-align: center;
            font-size: 10px;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        
        h1 {{
            font-size: 22px;
        }}
        
        h2 {{
            font-size: 18px;
        }}
        
        h3 {{
            font-size: 14px;
        }}
        
        section {{
            page-break-inside: avoid;
        }}
        
        .card {{
            page-break-inside: avoid;
        }}
        
        table {{
            page-break-inside: avoid;
        }}
        
        h1, h2, h3 {{
            page-break-after: avoid;
        }}
        
        @media print {{
            html, body {{
                width: 100%;
                background: #ffffff;
            }}
            
            * {{
                box-shadow: none !important;
                text-shadow: none !important;
            }}
            
            .container {{
                border-radius: 0;
            }}
            
            .header {{
                position: static;
            }}
            
            .section-divider {{
                background: #3b82f6;
            }}
            
            .metric-card, .card, .performer-card {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1 class="header-title">Market Minder Email Analytics Report</h1>
            <div class="header-meta">
                Report Period: {data['date_from']} to {data['date_to']} | Generated: {data['generated']}
            </div>
        </header>
        
        <main class="content">
            <section class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Emails Sent</div>
                    <div class="metric-value">{data['total_sent']}</div>
                    <div class="metric-subtext">All users combined</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Delivery Rate</div>
                    <div class="metric-value">{data['email_metrics']['delivery_rate']}%</div>
                    <div class="metric-subtext">Successfully delivered</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Days</div>
                    <div class="metric-value">{data['active_days']}</div>
                    <div class="metric-subtext">Days with activity</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Unique Senders</div>
                    <div class="metric-value">{data['unique_senders']}</div>
                    <div class="metric-subtext">Active email senders</div>
                </div>
            </section>
            
            <section class="section">
                <h2 class="section-title">User Status and Event Distribution</h2>
                <div class="section-divider"></div>
                <div class="grid-2">
                    <div class="card">
                        <h3 class="card-title">User Status Overview</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th class="numeric">Count</th>
                                    <th class="numeric">Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Total Registered</td>
                                    <td class="numeric">{data['total_users']}</td>
                                    <td class="numeric">100%</td>
                                </tr>
                                <tr>
                                    <td>Active Users</td>
                                    <td class="numeric">{data['active_users']}</td>
                                    <td class="numeric">{data['active_pct']}%</td>
                                </tr>
                                <tr>
                                    <td>Inactive Users</td>
                                    <td class="numeric">{data['inactive_users']}</td>
                                    <td class="numeric">{data['inactive_pct']}%</td>
                                </tr>
                                <tr>
                                    <td>Users with Activity</td>
                                    <td class="numeric">{data['users_with_activity']}</td>
                                    <td class="numeric">—</td>
                                </tr>
                                <tr>
                                    <td>Users No Activity</td>
                                    <td class="numeric">{data['users_no_activity']}</td>
                                    <td class="numeric">—</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="card">
                        <h3 class="card-title">Email Metrics Overview</h3>
"""
    
    metrics = data['email_metrics']
    max_value = metrics['sent']
    
    # Sent
    html += f"""                        <div class="bar-chart-row">
                            <div class="bar-label">Sent</div>
                            <div class="bar-container">
                                <div class="bar" style="width: 100%"></div>
                                <div class="bar-value">{metrics['sent']:,} (100%)</div>
                            </div>
                        </div>
                        <div class="bar-chart-row" style="margin-left: 130px; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 8px;">
                            Total emails sent from Market Minder
                        </div>
"""
    
    # Delivered
    delivered_width = (metrics['delivered'] / max_value * 100) if max_value > 0 else 0
    html += f"""                        <div class="bar-chart-row">
                            <div class="bar-label">Delivered</div>
                            <div class="bar-container">
                                <div class="bar" style="width: {delivered_width}%"></div>
                                <div class="bar-value">{metrics['delivered']:,} ({metrics['delivery_rate']}%)</div>
                            </div>
                        </div>
"""
    
    # Delivered note
    html += f"""                        <div class="bar-chart-row" style="margin-left: 130px; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 8px;">
                            Emails successfully reached recipient inboxes
                        </div>
"""
    
    # Opened
    opened_width = (metrics['opened'] / max_value * 100) if max_value > 0 else 0
    html += f"""                        <div class="bar-chart-row">
                            <div class="bar-label">Opened</div>
                            <div class="bar-container">
                                <div class="bar" style="width: {opened_width}%"></div>
                                <div class="bar-value">{metrics['opened']:,} ({metrics['engagement_rate']}%)</div>
                            </div>
                        </div>
"""
    
    # Opened note
    html += f"""                        <div class="bar-chart-row" style="margin-left: 130px; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 8px;">
                            Recipients who opened the email
                        </div>
"""
    
    # Failures
    failures_width = (metrics['failures'] / max_value * 100) if max_value > 0 else 0
    html += f"""                        <div class="bar-chart-row">
                            <div class="bar-label">Failures</div>
                            <div class="bar-container">
                                <div class="bar" style="width: {failures_width}%"></div>
                                <div class="bar-value">{metrics['failures']:,} ({metrics['failure_rate']}%)</div>
                            </div>
                        </div>
                        <div class="bar-chart-row" style="margin-left: 130px; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 8px;">
                            Emails that couldn't be delivered due to incorrect email addresses or temporary issues
                        </div>
"""
    
    # Unsubscribed
    unsub_width = (metrics['unsubscribed'] / max_value * 100) if max_value > 0 else 0
    html += f"""                        <div class="bar-chart-row">
                            <div class="bar-label">Unsubscribed</div>
                            <div class="bar-container">
                                <div class="bar" style="width: {unsub_width}%"></div>
                                <div class="bar-value">{metrics['unsubscribed']:,} ({metrics['unsubscribe_rate']}%)</div>
                            </div>
                        </div>
                        <div class="bar-chart-row" style="margin-left: 130px; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 8px;">
                            Recipients who opted out of future emails
                        </div>
"""
    
    html += """                    </div>
                </div>
            </section>
            
            <section class="section">
                <h2 class="section-title">Top Senders Activity</h2>
                <div class="section-divider"></div>
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>Sender Email</th>
                                <th>Registered</th>
                                <th class="numeric">Total Sent</th>
                                <th class="numeric">Active Days</th>
                                <th class="numeric">Avg/Day</th>
                                <th class="numeric">Max/Day</th>
                            </tr>
                        </thead>
                        <tbody>
"""
    
    for sender in data['top_senders']:
        badge_class = 'badge-yes' if sender['registered'] == 'Yes' else 'badge-no'
        html += f"""                            <tr>
                                <td>{sender['email']}</td>
                                <td><span class="badge {badge_class}">{sender['registered']}</span></td>
                                <td class="numeric">{sender['total_sent']}</td>
                                <td class="numeric">{sender['active_days']}</td>
                                <td class="numeric">{sender['avg_day']}</td>
                                <td class="numeric">{sender['max_day']}</td>
                            </tr>
"""
    
    html += """                        </tbody>
                    </table>
                </div>
            </section>
"""
    
    if data['weekly_freq']:
        all_dates = set()
        for user in data['weekly_freq']:
            all_dates.update(user['daily'].keys())
        sorted_dates = sorted(all_dates)
        
        html += """            
            <section class="section">
                <h2 class="section-title">Weekly Email Activity Pattern</h2>
                <div class="section-divider"></div>
                <div class="card heatmap-container">
                    <table class="heatmap-table">
                        <thead>
                            <tr>
                                <th>User Name</th>
"""
        
        for date in sorted_dates[:10]:
            html += f"                                <th class='numeric'>{date[-5:]}</th>\n"
        
        html += """                            </tr>
                        </thead>
                        <tbody>
"""
        
        max_val = max([max(user['daily'].values()) for user in data['weekly_freq'] if user['daily']], default=1)
        
        for user in data['weekly_freq'][:10]:
            html += f"                            <tr>\n                                <td>{user['name']}</td>\n"
            for date in sorted_dates[:10]:
                count = user['daily'].get(date, 0)
                
                if count == 0:
                    heat_class = 'heat-0'
                else:
                    normalized = count / max_val
                    if normalized <= 0.16:
                        heat_class = 'heat-1'
                    elif normalized <= 0.33:
                        heat_class = 'heat-2'
                    elif normalized <= 0.5:
                        heat_class = 'heat-3'
                    elif normalized <= 0.66:
                        heat_class = 'heat-4'
                    elif normalized <= 0.83:
                        heat_class = 'heat-5'
                    else:
                        heat_class = 'heat-6'
                
                display_val = f'{count:,}' if count > 0 else '—'
                html += f"                                <td class='{heat_class}'>{display_val}</td>\n"
            html += "                            </tr>\n"
        
        html += """                        </tbody>
                    </table>
                </div>
            </section>
"""
    
    html += """            
            <section class="section">
                <h2 class="section-title">User Email Volume</h2>
                <div class="section-divider"></div>
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>User Name</th>
                                <th>Status</th>
                                <th class="numeric">Sent</th>
                                <th class="numeric">Delivered</th>
                                <th>Delivery Rate</th>
                            </tr>
                        </thead>
                        <tbody>
"""
    
    for user in data['user_volume'][:15]:
        status_class = 'badge-active' if user['status'] == 'active' else 'badge-inactive'
        html += f"""                            <tr>
                                <td>{user['name']}</td>
                                <td><span class="badge {status_class}">{user['status'].upper()}</span></td>
                                <td class="numeric">{user['sent']}</td>
                                <td class="numeric">{user['delivered']}</td>
                                <td>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {user['rate']}%">{user['rate']:.1f}%</div>
                                    </div>
                                </td>
                            </tr>
"""
    
    html += """                        </tbody>
                    </table>
                </div>
            </section>
            
            <section class="section">
                <h2 class="section-title">Performance Analysis</h2>
                <div class="section-divider"></div>
                <div class="card">
                    <h3 class="card-title">Target Achievement Summary</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th class="numeric">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Total Emails Sent</td>
                                <td class="numeric">""" + data['total_sent'] + """</td>
                            </tr>
                            <tr>
                                <td>Total Expected (at 100%)</td>
                                <td class="numeric">""" + data['total_expected'] + """</td>
                            </tr>
                            <tr>
                                <td>Overall Achievement</td>
                                <td class="numeric">""" + f"{data['overall_achievement']:.1f}%" + """</td>
                            </tr>
                        </tbody>
                    </table>
                    <div style="margin-top: 24px;">
                        <div class="progress-bar" style="height: 32px;">
                            <div class="progress-fill" style="width: """ + f"{data['overall_achievement']}%" + """">""" + f"{data['overall_achievement']:.1f}% of Target" + """</div>
                        </div>
                    </div>
                </div>
            </section>
"""
    
    if data['top_volume'] or data['top_daily']:
        html += """            
            <section class="section">
                <h2 class="section-title">Top Performers</h2>
                <div class="section-divider"></div>
                <div class="top-performers-grid">
"""
        
        if data['top_volume']:
            html += """                    <div>
                        <h3 class="card-title">By Total Volume</h3>
"""
            for i, perf in enumerate(data['top_volume'], 1):
                html += f"""                        <div class="performer-card">
                            <div class="performer-rank">Rank {i}</div>
                            <div class="performer-name">{perf['name']}</div>
                            <div class="performer-value">{perf['value']} emails</div>
                        </div>
"""
            html += """                    </div>
"""
        
        if data['top_daily']:
            html += """                    <div>
                        <h3 class="card-title">By Daily Average</h3>
"""
            for i, perf in enumerate(data['top_daily'], 1):
                html += f"""                        <div class="performer-card">
                            <div class="performer-rank">Rank {i}</div>
                            <div class="performer-name">{perf['name']}</div>
                            <div class="performer-value">{perf['value']} emails/day</div>
                        </div>
"""
            html += """                    </div>
"""
        
        html += """                </div>
            </section>
"""
    
    engagement_pct = int(int(data['users_with_activity']) / int(data['total_users']) * 100) if int(data['total_users']) > 0 else 0
    top_performer = data['top_volume'][0]['name'] if data['top_volume'] else 'N/A'
    top_performer_val = data['top_volume'][0]['value'] if data['top_volume'] else '0'
    
    html += f"""            
            <section class="section">
                <h2 class="section-title">Key Observations</h2>
                <div class="section-divider"></div>
                <div class="card">
                    <ul class="observations-list">
                        <li>
                            <div class="observation-title">User Engagement</div>
                            <div class="observation-text">Only {data['users_with_activity']} out of {data['total_users']} registered users ({engagement_pct}%) showed email activity during this period.</div>
                        </li>
                        <li>
                            <div class="observation-title">Target Achievement</div>
                            <div class="observation-text">Overall target achievement is {data['overall_achievement']:.1f}%, indicating the team is performing below the 500 emails/user/day target.</div>
                        </li>
                        <li>
                            <div class="observation-title">Top Performer</div>
                            <div class="observation-text">{top_performer} leads with {top_performer_val} total emails sent.</div>
                        </li>
                        <li>
                            <div class="observation-title">Delivery Rate</div>
                            <div class="observation-text">Top performers maintain 96-100% delivery rates, indicating good email hygiene.</div>
                        </li>
                        <li>
                            <div class="observation-title">Active Days</div>
                            <div class="observation-text">The report covers {data['active_days']} days of activity from {data['date_from']} to {data['date_to']}.</div>
                        </li>
                    </ul>
                </div>
            </section>
        </main>
        
        <footer class="footer">
            <p>Generated on {data['generated']}</p>
            <p>Market Minder Email Analytics Report</p>
        </footer>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Corporate HTML report generated: {output_path}")


def main():
    print("Parsing report...")
    data = parse_report(INPUT_FILE)
    
    # Generate output filename based on date range
    try:
        date_from = datetime.strptime(data['date_from'], '%Y-%m-%d')
        date_to = datetime.strptime(data['date_to'], '%Y-%m-%d')
        start_str = date_from.strftime('%d_%b')
        end_str = date_to.strftime('%d_%b')
        # output_file = f"MM_Report_{start_str}_-_{end_str}.html"
        output_file = f"test.html"
    except:
        output_file = "MM_Report.html"
    
    print(f"Generating corporate HTML report: {output_file}")
    generate_html(data, output_file)
    
    print("Done!")


if __name__ == "__main__":
    main()
