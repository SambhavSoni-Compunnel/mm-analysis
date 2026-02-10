"""
Convert corporate HTML report to PDF using Playwright (browser-based)
This approach works reliably on Windows without GTK dependencies.

Installation:
    pip install playwright
    playwright install chromium
"""
from playwright.sync_api import sync_playwright
import os
import glob

def convert_html_to_pdf():
    """Convert the corporate HTML report to PDF using headless browser"""
    
    # Find the most recent MM_Report HTML file
    html_files = glob.glob("MM_Report_*.html")
    if not html_files:
        print("Error: No MM_Report_*.html file found")
        return
    
    # Use the most recently modified file
    INPUT_HTML = max(html_files, key=os.path.getmtime)
    OUTPUT_PDF = INPUT_HTML.replace('.html', '.pdf')
    
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
