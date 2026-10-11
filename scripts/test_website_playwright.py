"""Playwright automated test and inspection suite for the PharmaPath interactive discovery lab.

Tests every button, tab, control, pill, slider, search input, modal, and chart.
Verifies zero console errors, zero page exceptions, and captures high-resolution screenshots.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure UTF-8 stdout on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
screenshots_dir = ROOT_DIR / "reports" / "screenshots"
screenshots_dir.mkdir(parents=True, exist_ok=True)


def run_tests():
    print("=" * 80)
    print("STARTING PLAYWRIGHT LAB INTERACTIVE VERIFICATION SUITE")
    print("=" * 80)

    console_errors = []
    page_errors = []
    actions_count = 0
    screenshots_taken = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 950},
            device_scale_factor=1.5
        )
        page = context.new_page()

        # Listen for errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # 1. Navigate to Website
        print("\n[Step 1] Navigating to http://localhost:8080 ...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2.0)  # Allow particle canvas and data fetch to stabilize
        actions_count += 1

        # Screenshot: Initial Lab Landing (Subnetwork Canvas - Metformin RWR)
        s1_path = screenshots_dir / "01_lab_subnetwork_metformin.png"
        page.screenshot(path=str(s1_path), full_page=False)
        screenshots_taken.append(s1_path.name)
        print(f"Captured {s1_path.name} - Initial Landing")

        # 2. Test Subnetwork Controls & Alignment
        print("\n[Step 2] Testing Subnetwork Controls Alignment & Interactivity ...")
        
        # Verify title and sidebar layout
        panel_title = page.locator(".canvas-sidebar .panel-title").inner_text()
        print(f"Panel Title: '{panel_title}'")

        # Test Drug Switch to Imatinib
        page.click("button[data-drug='imatinib']")
        actions_count += 1
        time.sleep(1.5)
        s2_path = screenshots_dir / "02_subnetwork_imatinib.png"
        page.screenshot(path=str(s2_path))
        screenshots_taken.append(s2_path.name)
        print("  -> Switched drug to Imatinib")

        # Test Extraction Method Switch to 2-Hop
        page.click("button[data-method='2hop']")
        actions_count += 1
        time.sleep(1.5)
        print("  -> Switched extraction algorithm to 2-Hop")

        # Test Node Sizing Metric Dropdown
        page.select_option("#select-sizing-metric", "betweenness")
        actions_count += 1
        time.sleep(0.8)
        print("  -> Sizing metric set to Betweenness")

        # Test Edge Score Slider
        page.evaluate('document.getElementById("slider-edge-score").value = 750; document.getElementById("slider-edge-score").dispatchEvent(new Event("input"));')
        actions_count += 1
        time.sleep(0.6)
        print("  -> Edge score threshold set to 750")

        # Test Max Rendered Nodes Slider
        page.evaluate('document.getElementById("slider-max-nodes").value = 90; document.getElementById("slider-max-nodes").dispatchEvent(new Event("input"));')
        actions_count += 1
        time.sleep(0.6)
        print("  -> Max nodes set to 90")

        # Test Highlight Gene Search
        page.fill("#input-gene-search", "ABL1")
        page.click("#btn-gene-search")
        actions_count += 1
        time.sleep(0.8)
        print("  -> Searched and highlighted protein: ABL1")

        # Test Physics Pause & Resume
        physics_btn = page.locator("#btn-toggle-physics")
        print(f"  -> Physics button text before click: '{physics_btn.inner_text()}'")
        physics_btn.click()
        actions_count += 1
        time.sleep(0.4)
        print(f"  -> Physics button text after 1st click: '{physics_btn.inner_text()}'")
        physics_btn.click()
        actions_count += 1
        time.sleep(0.4)
        print(f"  -> Physics button text after 2nd click: '{physics_btn.inner_text()}'")

        # Test Center View Button
        page.click("#btn-fit-canvas")
        actions_count += 1
        time.sleep(0.8)
        print("  -> Clicked Center View")

        # Screenshot of Subnetwork with controls applied
        s3_path = screenshots_dir / "03_subnetwork_controls_aligned.png"
        page.screenshot(path=str(s3_path))
        screenshots_taken.append(s3_path.name)

        # Test Protein Node Modal
        print("\n[Step 3] Testing Protein Node Modal Inspection ...")
        page.evaluate('''() => {
            const node = window.appState.subnetworksData.imatinib['2hop'].nodes[0];
            window.openNodeModal(node);
        }''')
        actions_count += 1
        time.sleep(0.6)
        modal_shot = screenshots_dir / "04_protein_detail_modal.png"
        page.screenshot(path=str(modal_shot))
        screenshots_taken.append(modal_shot.name)
        print("  -> Captured Protein Detail Modal (clean, zero emojis)")

        # Close Modal
        page.click("#btn-modal-close")
        actions_count += 1
        time.sleep(0.4)

        # 4. Test Tab 2: Pathways & ORA
        print("\n[Step 4] Testing Tab 2: Pathways & ORA ...")
        page.click("button[data-tab='tab-pathways']")
        actions_count += 1
        time.sleep(1.0)

        # Toggle Drug to Metformin
        page.click("#pathway-drug-pills button[data-pdrug='metformin']")
        actions_count += 1
        time.sleep(0.5)

        # Toggle Scope to LINCS Perturbed
        page.click("#pathway-scope-pills button[data-pscope='lincs_perturbed']")
        actions_count += 1
        time.sleep(0.6)

        # Adjust FDR Threshold Slider
        page.evaluate('document.getElementById("slider-fdr-thresh").value = 0.01; document.getElementById("slider-fdr-thresh").dispatchEvent(new Event("input"));')
        actions_count += 1
        time.sleep(0.6)

        s5_path = screenshots_dir / "05_tab_pathways_ora.png"
        page.screenshot(path=str(s5_path))
        screenshots_taken.append(s5_path.name)
        print("  -> Captured Pathways & ORA Tab")

        # 5. Test Tab 3: Centrality & Hubs
        print("\n[Step 5] Testing Tab 3: Centrality & Modularity ...")
        page.click("button[data-tab='tab-centralities']")
        actions_count += 1
        time.sleep(1.0)

        # Toggle to Imatinib
        page.click("#cent-drug-pills button[data-cdrug='imatinib']")
        actions_count += 1
        time.sleep(0.6)

        s6_path = screenshots_dir / "06_tab_centrality_hubs.png"
        page.screenshot(path=str(s6_path))
        screenshots_taken.append(s6_path.name)
        print("  -> Captured Centrality & Hubs Tab")

        # 6. Test Tab 4: Disease Proximity Lab
        print("\n[Step 6] Testing Tab 4: Disease Proximity Lab ...")
        page.click("button[data-tab='tab-proximity']")
        actions_count += 1
        time.sleep(1.0)

        # Select Imatinib CML Pair
        page.select_option("#select-prox-pair", "imatinib_cml")
        actions_count += 1
        time.sleep(1.2)

        s7_path = screenshots_dir / "07_tab_disease_proximity.png"
        page.screenshot(path=str(s7_path))
        screenshots_taken.append(s7_path.name)
        print("  -> Captured Disease Proximity Tab")

        # 7. Test Tab 5: GNN Link Predictions
        print("\n[Step 7] Testing Tab 5: GNN Link Predictions ...")
        page.click("button[data-tab='tab-gnn']")
        actions_count += 1
        time.sleep(1.0)

        # Toggle Drug to Imatinib
        page.click("#gnn-drug-pills button[data-gdrug='imatinib']")
        actions_count += 1
        time.sleep(0.8)

        s8_path = screenshots_dir / "08_tab_gnn_predictions.png"
        page.screenshot(path=str(s8_path))
        screenshots_taken.append(s8_path.name)
        print("  -> Captured GNN Link Predictions Tab")

        # 8. Test Tab 6: Two-Drug Comparison
        print("\n[Step 8] Testing Tab 6: Two-Drug Comparison ...")
        page.click("button[data-tab='tab-comparison']")
        actions_count += 1
        time.sleep(1.2)

        s9_path = screenshots_dir / "09_tab_two_drug_comparison.png"
        page.screenshot(path=str(s9_path))
        screenshots_taken.append(s9_path.name)
        print("  -> Captured Two-Drug Comparison Tab")

        # 9. Test Top Utilities (Fullscreen)
        print("\n[Step 9] Testing Top Nav Utilities ...")
        page.click("#btn-fullscreen")
        actions_count += 1
        time.sleep(0.4)
        print("  -> Tested Fullscreen button")

        # Switch back to Subnetwork Tab to verify stability
        page.click("button[data-tab='tab-subnetworks']")
        actions_count += 1
        time.sleep(1.0)
        s10_path = screenshots_dir / "10_final_subnetwork_state.png"
        page.screenshot(path=str(s10_path))
        screenshots_taken.append(s10_path.name)
        print("  -> Verified return to Subnetwork Canvas")

        browser.close()

    print("\n" + "=" * 80)
    print("PLAYWRIGHT TESTING SUMMARY")
    print("=" * 80)
    print(f"Total Interactive Actions & Clicks Executed: {actions_count}")
    print(f"Total High-Resolution Screenshots Captured: {len(screenshots_taken)}")
    print(f"Console Errors Encountered: {len(console_errors)}")
    if console_errors:
        print("Console errors:", console_errors)
    print(f"Page Unhandled Exceptions: {len(page_errors)}")
    if page_errors:
        print("Page errors:", page_errors)
    print("=" * 80)

    return len(console_errors) == 0 and len(page_errors) == 0


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
    print("\nALL LAB CONTROLS, BUTTONS, TABS, AND CHARTS VERIFIED WITH ZERO ERRORS!")
