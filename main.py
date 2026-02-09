"""
Mailchimp Email Analytics Report Generator
Analyzes user activity and email delivery metrics from Mailchimp webhook data.
"""

import csv
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# File paths
USERS_FILE = "mm_users.csv"
EVENTS_FILE = "mailchimp_events_202602091659.csv"
OUTPUT_FILE = "email_analytics_report_v3.txt"

# Date filter - only include events from this date onwards
START_DATE = datetime(2026, 1, 25).date()

# Target emails per user per day
TARGET_EMAILS_PER_DAY = 500


def load_users(filepath):
    """Load user data from CSV file."""
    users = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row['email'].strip().lower()
            users[email] = {
                'firstname': row['firstname'],
                'lastname': row['lastname'],
                'name': f"{row['firstname']} {row['lastname']}",
                'creation_date': row['creation_date'],
                'role_id': row['role_id'],
                'status': row['status']
            }
    return users


def load_events(filepath):
    """Load mailchimp events from CSV file."""
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse the event timestamp
            try:
                event_ts = row['event_timestamp'].strip()
                if event_ts:
                    # Parse format: 2025-09-23 14:02:29.942
                    event_dt = datetime.strptime(event_ts.split('+')[0].strip(), '%Y-%m-%d %H:%M:%S.%f')
                else:
                    created_at = row['created_at'].strip()
                    event_dt = datetime.strptime(created_at.split('+')[0].strip(), '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    event_ts = row['event_timestamp'].strip() or row['created_at'].strip()
                    event_dt = datetime.strptime(event_ts.split('+')[0].strip(), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

            # Filter events before START_DATE
            if event_dt.date() < START_DATE:
                continue

            events.append({
                'id': row['id'],
                'event_type': row['event_type'].strip().lower(),
                'recipient_email': row['email'].strip().lower(),
                'sender': row['sender'].strip().lower() if row['sender'] else '',
                'subject': row['subject'],
                'event_datetime': event_dt,
                'event_date': event_dt.date(),
                'campaign_name': row.get('campaign_name', ''),
                'subaccount': row.get('subaccount', '')
            })
    return events


def get_week_key(date):
    """Get week identifier (year-week number)."""
    return f"{date.year}-W{date.isocalendar()[1]:02d}"


def get_email_username(email):
    """Extract username from email (part before @)."""
    if '@' in email:
        return email.split('@')[0].lower()
    return email.lower()


def analyze_data(users, events):
    """Perform comprehensive analysis of email data."""
    
    # Build mapping from username to user email (for cross-domain matching)
    # Users registered with @compunnel.us may send from @compunnel.com or @compunneldigital.com
    user_emails = set(users.keys())
    username_to_user = {get_email_username(email): email for email in user_emails}
    
    # Metrics storage
    user_send_events = defaultdict(list)  # sender -> list of send events
    user_delivered_events = defaultdict(list)  # sender -> list of delivered events
    user_daily_sends = defaultdict(lambda: defaultdict(int))  # sender -> date -> count
    user_daily_delivered = defaultdict(lambda: defaultdict(int))  # sender -> date -> count
    user_weekly_sends = defaultdict(lambda: defaultdict(int))  # sender -> week -> count
    user_weekly_delivered = defaultdict(lambda: defaultdict(int))  # sender -> week -> count
    
    # Also track all senders (including non-registered ones)
    all_sender_events = defaultdict(list)  # sender email -> events
    all_sender_daily = defaultdict(lambda: defaultdict(int))  # sender -> date -> count
    
    event_type_counts = defaultdict(int)
    all_dates = set()
    all_weeks = set()
    unique_senders = set()
    
    for event in events:
        sender = event['sender']
        event_type = event['event_type']
        event_date = event['event_date']
        week_key = get_week_key(event_date)
        
        event_type_counts[event_type] += 1
        all_dates.add(event_date)
        all_weeks.add(week_key)
        
        if sender:
            unique_senders.add(sender)
            
            # Track all sender activity
            if event_type == 'send':
                all_sender_events[sender].append(event)
                all_sender_daily[sender][event_date] += 1
        
        # Try to match sender to registered user (by exact email or username match)
        matched_user = None
        if sender in user_emails:
            matched_user = sender
        else:
            sender_username = get_email_username(sender)
            if sender_username in username_to_user:
                matched_user = username_to_user[sender_username]
        
        if matched_user:
            if event_type == 'send':
                user_send_events[matched_user].append(event)
                user_daily_sends[matched_user][event_date] += 1
                user_weekly_sends[matched_user][week_key] += 1
            elif event_type == 'delivered':
                user_delivered_events[matched_user].append(event)
                user_daily_delivered[matched_user][event_date] += 1
                user_weekly_delivered[matched_user][week_key] += 1
    
    return {
        'user_send_events': user_send_events,
        'user_delivered_events': user_delivered_events,
        'user_daily_sends': user_daily_sends,
        'user_daily_delivered': user_daily_delivered,
        'user_weekly_sends': user_weekly_sends,
        'user_weekly_delivered': user_weekly_delivered,
        'event_type_counts': event_type_counts,
        'all_dates': sorted(all_dates),
        'all_weeks': sorted(all_weeks),
        'unique_senders': unique_senders,
        'all_sender_events': all_sender_events,
        'all_sender_daily': all_sender_daily,
        'username_to_user': username_to_user
    }


def generate_report(users, events, analysis):
    """Generate the comprehensive report."""
    
    lines = []
    lines.append("=" * 80)
    lines.append("MAILCHIMP EMAIL ANALYTICS REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    # ===== SECTION 1: USER STATUS SUMMARY =====
    lines.append("-" * 80)
    lines.append("SECTION 1: ACTIVE / INACTIVE USERS")
    lines.append("-" * 80)
    
    active_users = {email: u for email, u in users.items() if u['status'] == 'active'}
    inactive_users = {email: u for email, u in users.items() if u['status'] == 'inactive'}
    
    lines.append(f"\nTotal Registered Users: {len(users)}")
    lines.append(f"Active Users: {len(active_users)} ({len(active_users)/len(users)*100:.1f}%)")
    lines.append(f"Inactive Users: {len(inactive_users)} ({len(inactive_users)/len(users)*100:.1f}%)")
    
    lines.append("\n-- Active Users List --")
    for i, (email, user) in enumerate(sorted(active_users.items()), 1):
        lines.append(f"  {i:3}. {user['name']:<35} | {email}")
    
    lines.append("\n-- Inactive Users List --")
    for i, (email, user) in enumerate(sorted(inactive_users.items()), 1):
        lines.append(f"  {i:3}. {user['name']:<35} | {email}")
    
    # ===== SECTION 2: OVERALL EVENT SUMMARY =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 2: OVERALL EVENT SUMMARY")
    lines.append("-" * 80)
    
    event_counts = analysis['event_type_counts']
    total_events = sum(event_counts.values())
    
    lines.append(f"\nTotal Events: {total_events:,}")
    for event_type, count in sorted(event_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  - {event_type.capitalize():<12}: {count:>8,} ({count/total_events*100:.1f}%)")
    
    if analysis['all_dates']:
        lines.append(f"\nDate Range: {min(analysis['all_dates'])} to {max(analysis['all_dates'])}")
        lines.append(f"Total Days with Activity: {len(analysis['all_dates'])}")
        lines.append(f"Total Weeks with Activity: {len(analysis['all_weeks'])}")
        lines.append(f"Unique Senders in Events: {len(analysis['unique_senders'])}")
    
    # ===== SECTION 2B: ALL SENDERS ACTIVITY (Including Non-Registered) =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 2B: ALL SENDERS ACTIVITY (Including Non-Registered)")
    lines.append("-" * 80)
    
    all_sender_stats = []
    for sender, sender_events in analysis['all_sender_events'].items():
        total_sent = len(sender_events)
        daily_data = analysis['all_sender_daily'].get(sender, {})
        active_days = len(daily_data)
        avg_per_day = total_sent / active_days if active_days > 0 else 0
        max_per_day = max(daily_data.values()) if daily_data else 0
        
        # Check if sender matches a registered user
        sender_username = get_email_username(sender)
        matched_user = analysis['username_to_user'].get(sender_username)
        is_registered = matched_user is not None
        
        all_sender_stats.append({
            'sender': sender,
            'total_sent': total_sent,
            'active_days': active_days,
            'avg_per_day': avg_per_day,
            'max_per_day': max_per_day,
            'is_registered': is_registered,
            'matched_user': matched_user,
            'daily_data': daily_data
        })
    
    all_sender_stats.sort(key=lambda x: -x['total_sent'])
    
    lines.append(f"\n{'Sender Email':<45} | {'Registered':^12} | {'Total Sent':>10} | {'Active Days':>11} | {'Avg/Day':>8} | {'Max/Day':>8}")
    lines.append("-" * 110)
    
    for stat in all_sender_stats:
        reg_status = "Yes" if stat['is_registered'] else "No"
        lines.append(
            f"{stat['sender']:<45} | {reg_status:^12} | {stat['total_sent']:>10,} | "
            f"{stat['active_days']:>11} | {stat['avg_per_day']:>8.1f} | {stat['max_per_day']:>8}"
        )
    
    registered_senders = [s for s in all_sender_stats if s['is_registered']]
    non_registered_senders = [s for s in all_sender_stats if not s['is_registered']]
    
    lines.append(f"\nTotal Active Senders: {len(all_sender_stats)}")
    lines.append(f"Registered Users Sending: {len(registered_senders)}")
    lines.append(f"Non-Registered Senders: {len(non_registered_senders)}")
    
    if non_registered_senders:
        lines.append("\n-- Non-Registered Senders (sending but not in users list) --")
        for i, stat in enumerate(non_registered_senders, 1):
            lines.append(f"  {i:3}. {stat['sender']:<45} | {stat['total_sent']:>8,} emails sent")
    
    # ===== SECTION 3: EMAILS PER USER SUMMARY =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 3: EMAILS SENT & DELIVERED PER USER")
    lines.append("-" * 80)
    
    user_stats = []
    for email, user in users.items():
        total_sent = len(analysis['user_send_events'].get(email, []))
        total_delivered = len(analysis['user_delivered_events'].get(email, []))
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        daily_sends = analysis['user_daily_sends'].get(email, {})
        daily_delivered = analysis['user_daily_delivered'].get(email, {})
        
        active_days = len(daily_sends)
        avg_per_day = total_sent / active_days if active_days > 0 else 0
        max_per_day = max(daily_sends.values()) if daily_sends else 0
        
        weekly_sends = analysis['user_weekly_sends'].get(email, {})
        active_weeks = len(weekly_sends)
        avg_per_week = total_sent / active_weeks if active_weeks > 0 else 0
        
        user_stats.append({
            'email': email,
            'name': user['name'],
            'status': user['status'],
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'delivery_rate': delivery_rate,
            'active_days': active_days,
            'avg_per_day': avg_per_day,
            'max_per_day': max_per_day,
            'active_weeks': active_weeks,
            'avg_per_week': avg_per_week,
            'daily_sends': daily_sends,
            'daily_delivered': daily_delivered,
            'weekly_sends': weekly_sends
        })
    
    # Sort by total sent (descending)
    user_stats.sort(key=lambda x: -x['total_sent'])
    
    lines.append("\n-- User Email Volume Summary (Sorted by Total Sent) --")
    lines.append(f"\n{'User Name':<30} | {'Status':<8} | {'Total Sent':>10} | {'Delivered':>10} | {'Del.Rate':>8} | {'Active Days':>11} | {'Avg/Day':>8} | {'Max/Day':>8}")
    lines.append("-" * 120)
    
    for stat in user_stats:
        lines.append(
            f"{stat['name']:<30} | {stat['status']:<8} | {stat['total_sent']:>10,} | "
            f"{stat['total_delivered']:>10,} | {stat['delivery_rate']:>7.1f}% | "
            f"{stat['active_days']:>11} | {stat['avg_per_day']:>8.1f} | {stat['max_per_day']:>8}"
        )
    
    # Users with no email activity
    no_activity_users = [s for s in user_stats if s['total_sent'] == 0]
    active_email_users = [s for s in user_stats if s['total_sent'] > 0]
    
    lines.append(f"\nUsers with Email Activity: {len(active_email_users)}")
    lines.append(f"Users with No Email Activity: {len(no_activity_users)}")
    
    if no_activity_users:
        lines.append("\n-- Users with No Email Activity --")
        for i, stat in enumerate(no_activity_users, 1):
            lines.append(f"  {i:3}. {stat['name']:<35} | {stat['email']:<40} | Status: {stat['status']}")
    
    # ===== SECTION 4: DAILY FREQUENCY ANALYSIS =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 4: DAILY EMAIL FREQUENCY PER USER")
    lines.append("-" * 80)
    
    lines.append(f"\nTarget: {TARGET_EMAILS_PER_DAY} emails per user per day")
    
    for stat in user_stats:
        if stat['total_sent'] == 0:
            continue
            
        lines.append(f"\n>>> {stat['name']} ({stat['email']}) - Status: {stat['status'].upper()}")
        lines.append(f"    Total Sent: {stat['total_sent']:,} | Total Delivered: {stat['total_delivered']:,} | Active Days: {stat['active_days']}")
        
        daily_data = stat['daily_sends']
        daily_delivered = stat['daily_delivered']
        
        if daily_data:
            lines.append(f"\n    {'Date':<12} | {'Sent':>8} | {'Delivered':>10} | {'vs Target':>10} | {'Performance':>12}")
            lines.append("    " + "-" * 60)
            
            for date in sorted(daily_data.keys()):
                sent = daily_data[date]
                delivered = daily_delivered.get(date, 0)
                diff = sent - TARGET_EMAILS_PER_DAY
                pct = (sent / TARGET_EMAILS_PER_DAY) * 100
                perf = "ABOVE" if diff >= 0 else "BELOW"
                lines.append(f"    {str(date):<12} | {sent:>8,} | {delivered:>10,} | {diff:>+10,} | {pct:>6.1f}% ({perf})")
    
    # ===== SECTION 5: WEEKLY FREQUENCY ANALYSIS =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 5: WEEKLY EMAIL FREQUENCY PER USER")
    lines.append("-" * 80)
    
    weekly_target = TARGET_EMAILS_PER_DAY * 5  # 5 working days
    lines.append(f"\nWeekly Target (5 working days): {weekly_target:,} emails per user per week")
    
    for stat in user_stats:
        if stat['total_sent'] == 0:
            continue
            
        lines.append(f"\n>>> {stat['name']} ({stat['email']})")
        
        weekly_data = stat['weekly_sends']
        weekly_delivered = analysis['user_weekly_delivered'].get(stat['email'], {})
        
        if weekly_data:
            lines.append(f"\n    {'Week':<10} | {'Sent':>8} | {'Delivered':>10} | {'vs Target':>12} | {'Performance':>12}")
            lines.append("    " + "-" * 60)
            
            for week in sorted(weekly_data.keys()):
                sent = weekly_data[week]
                delivered = weekly_delivered.get(week, 0)
                diff = sent - weekly_target
                pct = (sent / weekly_target) * 100
                perf = "ABOVE" if diff >= 0 else "BELOW"
                lines.append(f"    {week:<10} | {sent:>8,} | {delivered:>10,} | {diff:>+12,} | {pct:>6.1f}% ({perf})")
    
    # ===== SECTION 6: TARGET COMPARISON SUMMARY =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 6: TARGET COMPARISON SUMMARY (500 Emails/User/Day)")
    lines.append("-" * 80)
    
    lines.append(f"\nDaily Target: {TARGET_EMAILS_PER_DAY} emails per user per day")
    lines.append(f"Weekly Target (5 days): {weekly_target:,} emails per user per week")
    
    # Calculate overall performance
    total_possible_days = len(analysis['all_dates']) * len(active_email_users) if active_email_users else 0
    total_expected_emails = total_possible_days * TARGET_EMAILS_PER_DAY
    total_actual_emails = sum(s['total_sent'] for s in user_stats)
    
    lines.append(f"\n-- Overall Performance --")
    lines.append(f"Total Emails Sent (all users): {total_actual_emails:,}")
    if total_expected_emails > 0:
        lines.append(f"Total Expected (at 100% target): {total_expected_emails:,}")
        lines.append(f"Overall Achievement: {(total_actual_emails/total_expected_emails)*100:.1f}%")
    
    # Per-user target achievement
    lines.append(f"\n-- Per-User Daily Target Achievement --")
    lines.append(f"\n{'User Name':<30} | {'Avg/Day':>10} | {'Target':>8} | {'Achievement':>12} | {'Status':<15}")
    lines.append("-" * 90)
    
    for stat in user_stats:
        if stat['active_days'] > 0:
            achievement = (stat['avg_per_day'] / TARGET_EMAILS_PER_DAY) * 100
            if achievement >= 100:
                status = "TARGET MET"
            elif achievement >= 75:
                status = "NEAR TARGET"
            elif achievement >= 50:
                status = "BELOW TARGET"
            else:
                status = "SIGNIFICANTLY BELOW"
        else:
            achievement = 0
            status = "NO ACTIVITY"
        
        lines.append(
            f"{stat['name']:<30} | {stat['avg_per_day']:>10.1f} | {TARGET_EMAILS_PER_DAY:>8} | "
            f"{achievement:>10.1f}% | {status:<15}"
        )
    
    # Days meeting target analysis
    lines.append(f"\n-- Days Meeting Target (>= {TARGET_EMAILS_PER_DAY} emails) --")
    
    for stat in user_stats:
        if stat['total_sent'] == 0:
            continue
        
        daily_data = stat['daily_sends']
        days_at_target = sum(1 for sent in daily_data.values() if sent >= TARGET_EMAILS_PER_DAY)
        total_days = len(daily_data)
        pct_days_at_target = (days_at_target / total_days * 100) if total_days > 0 else 0
        
        lines.append(f"  {stat['name']:<35}: {days_at_target}/{total_days} days ({pct_days_at_target:.1f}%) at or above target")
    
    # ===== SECTION 7: TOP PERFORMERS =====
    lines.append("")
    lines.append("-" * 80)
    lines.append("SECTION 7: TOP PERFORMERS & STATISTICS")
    lines.append("-" * 80)
    
    active_stats = [s for s in user_stats if s['total_sent'] > 0]
    
    if active_stats:
        # Top by total volume
        top_volume = sorted(active_stats, key=lambda x: -x['total_sent'])[:5]
        lines.append("\n-- Top 5 by Total Email Volume --")
        for i, stat in enumerate(top_volume, 1):
            lines.append(f"  {i}. {stat['name']:<30} | {stat['total_sent']:>10,} emails")
        
        # Top by daily average
        top_avg = sorted(active_stats, key=lambda x: -x['avg_per_day'])[:5]
        lines.append("\n-- Top 5 by Daily Average --")
        for i, stat in enumerate(top_avg, 1):
            lines.append(f"  {i}. {stat['name']:<30} | {stat['avg_per_day']:>10.1f} emails/day")
        
        # Top by max single day
        top_max = sorted(active_stats, key=lambda x: -x['max_per_day'])[:5]
        lines.append("\n-- Top 5 by Max Single Day --")
        for i, stat in enumerate(top_max, 1):
            lines.append(f"  {i}. {stat['name']:<30} | {stat['max_per_day']:>10,} emails")
        
        # Best delivery rate
        stats_with_sends = [s for s in active_stats if s['total_sent'] > 0]
        top_delivery = sorted(stats_with_sends, key=lambda x: -x['delivery_rate'])[:5]
        lines.append("\n-- Top 5 by Delivery Rate --")
        for i, stat in enumerate(top_delivery, 1):
            lines.append(f"  {i}. {stat['name']:<30} | {stat['delivery_rate']:>10.1f}%")
    
    # ===== FOOTER =====
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def main():
    """Main function to run the analysis and generate report."""
    print("Loading user data...")
    users = load_users(USERS_FILE)
    print(f"  Loaded {len(users)} users")
    
    print("Loading event data...")
    events = load_events(EVENTS_FILE)
    print(f"  Loaded {len(events)} events")
    
    print("Analyzing data...")
    analysis = analyze_data(users, events)
    
    print("Generating report...")
    report = generate_report(users, events, analysis)
    
    print(f"Saving report to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport generated successfully: {OUTPUT_FILE}")
    print(f"Total lines: {len(report.splitlines())}")


if __name__ == "__main__":
    main()
