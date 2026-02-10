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
    """Convert the corporate HTML reports to PDF using headless browser"""
    
    # Find MM_Report HTML files for both MM Team and Client
    # mm_team_files = glob.glob("*_for_MM_Team.html")
    mm_team_files = ("test_for_MM_Team.html")
    client_files =  ("test_for_Client.html")
    
    html_files = []
    
    # Add the most recent MM Team file
    if mm_team_files:
        html_files.append(max(mm_team_files, key=os.path.getmtime))
    
    # Add the most recent Client file
    if client_files:
        html_files.append(max(client_files, key=os.path.getmtime))
    
    if not html_files:
        print("Error: No MM_Report HTML files found")
        return
    
    with sync_playwright() as p:
        # Launch headless browser once for both conversions
        browser = p.chromium.launch()
        
        for INPUT_HTML in html_files:
            OUTPUT_PDF = INPUT_HTML.replace('.html', '.pdf')
            
            # Get absolute path to HTML file
            html_path = os.path.abspath(INPUT_HTML)
            
            if not os.path.exists(html_path):
                print(f"Error: {INPUT_HTML} not found")
                continue
            
            print(f"Converting {INPUT_HTML} to PDF...")
            
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
            
            page.close()
            print(f"✓ PDF generated: {OUTPUT_PDF}")
        
        browser.close()
    
    print(f"\n✓ All PDFs generated successfully!")

if __name__ == "__main__":
    convert_html_to_pdf()
