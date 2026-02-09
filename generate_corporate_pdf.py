"""
Convert corporate HTML report to PDF using WeasyPrint
"""
from weasyprint import HTML

INPUT_HTML = "email_analytics_report_corporate.html"
OUTPUT_PDF = "email_analytics_report_corporate.pdf"

def convert_html_to_pdf():
    """Convert the corporate HTML report to PDF format"""
    print(f"Reading {INPUT_HTML}...")
    
    # Convert HTML to PDF
    HTML(INPUT_HTML).write_pdf(OUTPUT_PDF)
    
    print(f"✓ PDF generated successfully: {OUTPUT_PDF}")

if __name__ == "__main__":
    convert_html_to_pdf()
