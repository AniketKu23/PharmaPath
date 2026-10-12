import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"name": "mobile_narrow", "width": 360, "height": 640},
    {"name": "mobile_iphone", "width": 390, "height": 844},
    {"name": "mobile_large",  "width": 430, "height": 932},
    {"name": "tablet",        "width": 768, "height": 1024},
    {"name": "desktop",       "width": 1280, "height": 800},
]

PAGES = [
    {"name": "Overview", "path": "/"},
    {"name": "Drug_Explorer", "path": "/Drug_Explorer"},
    {"name": "Pathways", "path": "/Pathways"},
    {"name": "Network_Metrics", "path": "/Network_Metrics"},
    {"name": "Disease_Proximity", "path": "/Disease_Proximity"},
    {"name": "Link_Predictions", "path": "/Link_Predictions"},
    {"name": "Drug_Comparison", "path": "/Drug_Comparison"},
]

OUTPUT_DIR = os.path.abspath("reports/mobile/after")

async def run_after_audit():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for vp in VIEWPORTS:
            w, h = vp["width"], vp["height"]
            print(f"\n==========================================")
            print(f"Capturing After Viewport: {vp['name']} ({w}x{h})")
            print(f"==========================================")
            
            context = await browser.new_context(
                viewport={"width": w, "height": h},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1" if w < 768 else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            for pg in PAGES:
                page_name = pg["name"]
                url = f"http://127.0.0.1:8501{pg['path']}"
                print(f"Loading {page_name} at {url}...")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                except Exception as e:
                    print(f"  Warning: navigation timeout: {e}")
                
                # Wait for Streamlit app container and stabilization
                await page.wait_for_timeout(3500)
                
                # Measure layout properties
                audit_info = await page.evaluate('''() => {
                    const scrollWidth = document.documentElement.scrollWidth;
                    const innerWidth = window.innerWidth;
                    const hasHorizontalOverflow = scrollWidth > innerWidth + 1;

                    // Tap target measurement
                    const interactiveElements = document.querySelectorAll('button, a, input, select, [role="button"], [role="tab"]');
                    let smallTargetCount = 0;
                    let totalTargets = 0;
                    interactiveElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            totalTargets++;
                            if (rect.width < 40 || rect.height < 40) { // standard tolerance check
                                smallTargetCount++;
                            }
                        }
                    });

                    // Check iframes
                    const iframes = [];
                    document.querySelectorAll('iframe').forEach(ifr => {
                        const r = ifr.getBoundingClientRect();
                        iframes.push({
                            width: Math.round(r.width),
                            height: Math.round(r.height)
                        });
                    });

                    return {
                        scrollWidth,
                        innerWidth,
                        hasHorizontalOverflow,
                        overflowDiff: Math.max(0, scrollWidth - innerWidth),
                        totalTargets,
                        smallTargetCount,
                        iframes
                    };
                }''')

                screenshot_path = os.path.join(OUTPUT_DIR, f"{page_name}_{w}x{h}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  Saved screenshot: {screenshot_path}")
                print(f"  Horizontal overflow: {audit_info['hasHorizontalOverflow']} (diff: {audit_info['overflowDiff']}px)")
                if audit_info['iframes']:
                    print(f"  Iframes: {audit_info['iframes']}")

                results.append({
                    "viewport": vp["name"],
                    "width": w,
                    "height": h,
                    "page": page_name,
                    "screenshot": f"{page_name}_{w}x{h}.png",
                    "metrics": audit_info
                })

            await context.close()

        await browser.close()

    summary_json_path = os.path.join(OUTPUT_DIR, "audit_metrics.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll 35 AFTER screenshots and metrics saved to {summary_json_path}")

if __name__ == "__main__":
    asyncio.run(run_after_audit())
