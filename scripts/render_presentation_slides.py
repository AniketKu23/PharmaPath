"""Render each slide in presentation_deck/index.html to a high-resolution PNG image."""

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
DECK_HTML = ROOT_DIR / "reports" / "presentation_deck" / "index.html"
OUT_DIR = ROOT_DIR / "reports" / "presentation_deck" / "slides_rendered"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def render_slides():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use exact 1920x1080 viewport
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1.0)

        file_url = DECK_HTML.as_uri()
        print(f"Loading {file_url}...")
        page.goto(file_url, wait_until="networkidle")

        slide_elements = page.locator(".slide-wrapper").all()
        print(f"Found {len(slide_elements)} slides to render.")

        for idx, slide in enumerate(slide_elements):
            slide_id = slide.get_attribute("id") or f"slide_{idx:02d}"
            out_file = OUT_DIR / f"{slide_id}.png"
            # Screenshot the specific slide bounding box
            slide.screenshot(path=str(out_file))
            print(f"Rendered [{idx + 1}/{len(slide_elements)}]: {out_file.name}")

        browser.close()
        print("All slides rendered successfully!")

if __name__ == "__main__":
    render_slides()
