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

OUTPUT_DIR = os.path.abspath("reports/mobile/before")

async def run_audit():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for vp in VIEWPORTS:
            w, h = vp["width"], vp["height"]
            print(f"\n==========================================")
            print(f"Auditing Viewport: {vp['name']} ({w}x{h})")
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
                    print(f"  Warning: navigation timeout or issue: {e}")
                
                # Wait for Streamlit app container and stabilization
                await page.wait_for_timeout(3500)
                
                # Measure layout properties
                audit_info = await page.evaluate('''() => {
                    const scrollWidth = document.documentElement.scrollWidth;
                    const innerWidth = window.innerWidth;
                    const hasHorizontalOverflow = scrollWidth > innerWidth + 1; // 1px threshold for subpixel

                    // Find elements causing horizontal overflow
                    const overflowingElements = [];
                    const allEls = document.querySelectorAll('*');
                    allEls.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > innerWidth + 2) {
                            overflowingElements.push({
                                tag: el.tagName,
                                class: el.className,
                                testid: el.getAttribute('data-testid') || '',
                                width: Math.round(rect.width),
                                right: Math.round(rect.right),
                                text: (el.innerText || '').slice(0, 50).trim()
                            });
                        }
                    });

                    // Measure interactive tap target sizes (buttons, inputs, selects, tabs)
                    const interactiveTargets = [];
                    const interactiveElements = document.querySelectorAll('button, a, input, select, [role="button"], [role="tab"], [data-testid="stSelectbox"]');
                    let smallTargetCount = 0;
                    interactiveElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            const isSmall = rect.width < 44 || rect.height < 44;
                            if (isSmall) {
                                smallTargetCount++;
                            }
                            interactiveTargets.push({
                                tag: el.tagName,
                                testid: el.getAttribute('data-testid') || '',
                                text: (el.innerText || el.getAttribute('aria-label') || '').slice(0, 30).trim(),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                isSmall: isSmall
                            });
                        }
                    });

                    // Check iframes (e.g., PyVis)
                    const iframes = [];
                    document.querySelectorAll('iframe').forEach(ifr => {
                        const r = ifr.getBoundingClientRect();
                        iframes.push({
                            width: Math.round(r.width),
                            height: Math.round(r.height),
                            src: ifr.src ? ifr.src.slice(0, 50) : '',
                            title: ifr.title || ''
                        });
                    });

                    // Check tables / dataframes
                    const tables = [];
                    document.querySelectorAll('[data-testid="stDataFrame"], table').forEach(tbl => {
                        const r = tbl.getBoundingClientRect();
                        tables.push({
                            width: Math.round(r.width),
                            height: Math.round(r.height),
                            exceedsViewport: r.width > innerWidth
                        });
                    });

                    return {
                        scrollWidth,
                        innerWidth,
                        hasHorizontalOverflow,
                        overflowDiff: Math.max(0, scrollWidth - innerWidth),
                        overflowingElementCount: overflowingElements.length,
                        sampleOverflowingElements: overflowingElements.slice(0, 5),
                        totalInteractiveTargets: interactiveTargets.length,
                        smallTargetCount,
                        smallTargetRatio: interactiveTargets.length > 0 ? (smallTargetCount / interactiveTargets.length) : 0,
                        iframes,
                        tables
                    };
                }''')

                screenshot_path = os.path.join(OUTPUT_DIR, f"{page_name}_{w}x{h}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"  Saved screenshot: {screenshot_path}")
                print(f"  Horizontal overflow: {audit_info['hasHorizontalOverflow']} (scrollWidth: {audit_info['scrollWidth']}, viewport: {audit_info['innerWidth']}, diff: {audit_info['overflowDiff']}px)")
                print(f"  Small tap targets: {audit_info['smallTargetCount']} / {audit_info['totalInteractiveTargets']} ({audit_info['smallTargetRatio']*100:.1f}%)")
                if audit_info['iframes']:
                    print(f"  Iframes detected: {len(audit_info['iframes'])} -> {audit_info['iframes']}")

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
    print(f"\nAll 35 screenshots and audit metrics successfully written to {summary_json_path}")

if __name__ == "__main__":
    asyncio.run(run_audit())
