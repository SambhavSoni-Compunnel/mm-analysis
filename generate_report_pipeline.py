"""
Main report generation pipeline
Orchestrates the complete flow: CSV -> TXT -> HTML -> PDF
"""

import subprocess
import sys
import os
from datetime import datetime
import glob


def step1_process_csv_data():
    """
    Step 1: Process CSV files and generate text report
    TODO: Implement CSV processing logic
    - Read mm_users.csv
    - Read mailchimp_events CSV
    - Generate analytics
    - Output: test/email_analytics_report_v3.txt
    """
    print("\n" + "="*60)
    print("STEP 1: Processing CSV Data")
    print("="*60)
    
    # For now, skip this step - assuming txt file already exists
    print("⏭️  Skipping CSV processing (implement later)")
    print("   Assuming test/email_analytics_report_v3.txt already exists")
    
    # Verify the txt file exists
    txt_file = "test/email_analytics_report_v3.txt"
    if not os.path.exists(txt_file):
        print(f"❌ Error: {txt_file} not found")
        return False
    
    print(f"✓ Text report found: {txt_file}")
    return True


def step2_generate_html():
    """
    Step 2: Convert text report to HTML
    Runs: generate_corporate_html_report.py
    Output: MM_Report_DD_Mon_-_DD_Mon.html
    """
    print("\n" + "="*60)
    print("STEP 2: Generating HTML Report")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, "generate_corporate_html_report.py"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✓ HTML report generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating HTML: {e}")
        print(e.stderr)
        return False


def step3_generate_pdf():
    """
    Step 3: Convert HTML report to PDF
    Runs: generate_corporate_pdf_browser.py
    Output: MM_Report_DD_Mon_-_DD_Mon.pdf
    """
    print("\n" + "="*60)
    print("STEP 3: Generating PDF Report")
    print("="*60)
    
    # Verify HTML file exists
    html_files = glob.glob("MM_Report_*.html")
    if not html_files:
        print("❌ Error: No HTML report found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "generate_corporate_pdf_browser.py"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✓ PDF report generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating PDF: {e}")
        print(e.stderr)
        return False


def main():
    """
    Main pipeline orchestration
    """
    print("\n" + "="*60)
    print("📊 MAILCHIMP ANALYTICS REPORT GENERATOR")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Process CSV data (skipped for now)
    if not step1_process_csv_data():
        print("\n❌ Pipeline failed at Step 1")
        sys.exit(1)
    
    # Step 2: Generate HTML
    if not step2_generate_html():
        print("\n❌ Pipeline failed at Step 2")
        sys.exit(1)
    
    # Step 3: Generate PDF
    if not step3_generate_pdf():
        print("\n❌ Pipeline failed at Step 3")
        sys.exit(1)
    
    # Success
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    
    # List generated files
    html_files = glob.glob("MM_Report_*.html")
    pdf_files = glob.glob("MM_Report_*.pdf")
    
    print("\n📁 Generated Files:")
    for f in html_files:
        print(f"   • {f}")
    for f in pdf_files:
        print(f"   • {f}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
