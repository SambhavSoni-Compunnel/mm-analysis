"""
Convert corporate HTML report to PDF using Playwright (browser-based)
This approach works reliably on Windows without GTK dependencies.

Installation:
    pip install playwright
    playwright install chromium
"""
from playwright.sync_api import sync_playwright
import os

INPUT_HTML = "email_analytics_report_corporate.html"
OUTPUT_PDF = "email_analytics_report_corporate.pdf"

def convert_html_to_pdf():
    """Convert the corporate HTML report to PDF using headless browser"""
    
    # Get absolute path to HTML file
    html_path = os.path.abspath(INPUT_HTML)
    
    if not os.path.exists(html_path):
        print(f"Error: {INPUT_HTML} not found")
        return
    
    print(f"Reading {INPUT_HTML}...")
    
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Load HTML file
        page.goto(f"file:///{html_path}")
        
        # Wait for page to be fully loaded
        page.wait_for_load_state("networkidle")
        
        # Generate PDF with print-optimized settings
        page.pdf(
            path=OUTPUT_PDF,
            format="Letter",
            margin={
                "top": "0.5in",
                "right": "0.75in",
                "bottom": "0.5in",
                "left": "0.75in"
            },
            print_background=True,
            prefer_css_page_size=False
        )
        
        browser.close()
    
    print(f"✓ PDF generated successfully: {OUTPUT_PDF}")

if __name__ == "__main__":
    convert_html_to_pdf()
