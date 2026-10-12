"""Automated Mobile UI & Usability Regression Tests (Playwright Synchronous).

Verifies that all 7 PharmaPath Streamlit pages render cleanly at mobile viewport (390x844),
have zero horizontal overflow, zero unhandled JavaScript errors, and responsive controls.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8501"

PAGES = [
    {"name": "Overview", "path": "/"},
    {"name": "Drug Explorer", "path": "/Drug_Explorer"},
    {"name": "Pathways", "path": "/Pathways"},
    {"name": "Network Metrics", "path": "/Network_Metrics"},
    {"name": "Disease Proximity", "path": "/Disease_Proximity"},
    {"name": "Link Predictions", "path": "/Link_Predictions"},
    {"name": "Drug Comparison", "path": "/Drug_Comparison"},
    {"name": "Methodology Guide", "path": "/Methodology_Guide"},
]


def test_mobile_pages_no_overflow_and_no_js_errors():
    """Verify mobile rendering at 390x844 with control interactions."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page = context.new_page()

        js_errors: list[tuple[str, str]] = []
        page.on("pageerror", lambda err: js_errors.append((page.url, str(err))))

        for pg in PAGES:
            target_url = f"{BASE_URL}{pg['path']}"
            response = page.goto(target_url, wait_until="networkidle", timeout=30000)
            assert response is not None and response.status == 200, f"Failed to load {target_url}"

            page.wait_for_timeout(2500)

            # Assert no horizontal overflow
            scroll_width, inner_width = page.evaluate(
                "() => [document.documentElement.scrollWidth, window.innerWidth]"
            )
            assert scroll_width <= inner_width + 1, (
                f"Page {pg['name']} has horizontal overflow: scrollWidth={scroll_width} > innerWidth={inner_width}"
            )

            # Interact with at least one control per page
            if pg["path"] == "/":
                btn = page.locator("a.pp-back-to-top").first
                assert btn.count() >= 1, "Back to Top button missing on Overview"

            elif pg["path"] == "/Drug_Explorer":
                list_radio = page.get_by_text("Low-Bandwidth List View").first
                if list_radio.count() > 0:
                    list_radio.click()
                    page.wait_for_timeout(800)

            elif pg["path"] == "/Pathways":
                summary = page.locator("summary").first
                if summary.count() > 0:
                    summary.click()
                    page.wait_for_timeout(800)

            elif pg["path"] == "/Network_Metrics":
                tab2 = page.get_by_role("tab", name="Top Bottleneck & Bridge Table").first
                if tab2.count() > 0:
                    tab2.click()
                    page.wait_for_timeout(800)

            elif pg["path"] == "/Disease_Proximity":
                select_box = page.locator('[data-testid="stSelectbox"]').first
                assert select_box.count() >= 1

            elif pg["path"] == "/Link_Predictions":
                tab_hyp = page.get_by_role("tab", name="Top-20 Hypotheses & Evidence").first
                if tab_hyp.count() > 0:
                    tab_hyp.click()
                    page.wait_for_timeout(800)

            elif pg["path"] == "/Drug_Comparison":
                tab_shared = page.get_by_role("tab", name="Shared Cross-Talk Proteins").first
                if tab_shared.count() > 0:
                    tab_shared.click()
                    page.wait_for_timeout(800)

        # Assert no unhandled JavaScript runtime exceptions occurred
        assert len(js_errors) == 0, f"JavaScript runtime errors detected: {js_errors}"

        context.close()
        browser.close()
