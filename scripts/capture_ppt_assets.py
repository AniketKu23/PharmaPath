"""Capture pristine, high-resolution screenshots of every section and tab of the live PharmaPath website."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT_DIR / "reports" / "ppt_assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.5
        )
        page = context.new_page()

        print("Navigating to http://localhost:8080...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2.5)

        # 1. Metformin Subnetwork Canvas
        print("Capturing Metformin Subnetwork Canvas...")
        page.click("button[data-tab='tab-subnetworks']")
        page.click("button[data-drug='metformin']")
        page.click("button[data-method='rwr']")
        page.click("#btn-fit-canvas")
        time.sleep(2.0)
        page.screenshot(path=str(OUT_DIR / "01_subnetwork_metformin.png"))

        # 2. Imatinib Subnetwork Canvas
        print("Capturing Imatinib Subnetwork Canvas...")
        page.click("button[data-drug='imatinib']")
        page.click("button[data-method='rwr']")
        page.click("#btn-fit-canvas")
        time.sleep(2.0)
        page.screenshot(path=str(OUT_DIR / "02_subnetwork_imatinib.png"))

        # 3. Protein Modal Inspection (BCR-ABL1 or KIT)
        print("Capturing Protein Modal...")
        page.evaluate('''() => {
            const node = window.appState.subnetworksData.imatinib['rwr'].nodes.find(n => n.symbol === 'KIT' || n.symbol === 'ABL1') || window.appState.subnetworksData.imatinib['rwr'].nodes[0];
            window.openNodeModal(node);
        }''')
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "03_protein_modal.png"))
        page.click("#btn-modal-close")
        time.sleep(0.5)

        # 4. Pathways Tab - Metformin RWR
        print("Capturing Pathways Tab (Metformin)...")
        page.click("button[data-tab='tab-pathways']")
        time.sleep(1.0)
        page.click("#pathway-drug-pills button[data-pdrug='metformin']")
        page.click("#pathway-scope-pills button[data-pscope='rwr_subnetwork']")
        page.evaluate('document.getElementById("slider-fdr-thresh").value = 0.05; document.getElementById("slider-fdr-thresh").dispatchEvent(new Event("input"));')
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "04_pathways_metformin.png"))

        # 5. Pathways Tab - Imatinib RWR
        print("Capturing Pathways Tab (Imatinib)...")
        page.click("#pathway-drug-pills button[data-pdrug='imatinib']")
        page.click("#pathway-scope-pills button[data-pscope='rwr_subnetwork']")
        page.evaluate('document.getElementById("slider-fdr-thresh").value = 0.05; document.getElementById("slider-fdr-thresh").dispatchEvent(new Event("input"));')
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "05_pathways_imatinib.png"))

        # 6. Centralities Tab - Metformin
        print("Capturing Centralities Tab (Metformin)...")
        page.click("button[data-tab='tab-centralities']")
        time.sleep(1.0)
        page.click("#cent-drug-pills button[data-cdrug='metformin']")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "06_centralities_metformin.png"))

        # 7. Centralities Tab - Imatinib
        print("Capturing Centralities Tab (Imatinib)...")
        page.click("#cent-drug-pills button[data-cdrug='imatinib']")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "07_centralities_imatinib.png"))

        # 8. Disease Proximity Tab - Metformin -> T2D
        print("Capturing Disease Proximity Tab (Metformin -> T2D)...")
        page.click("button[data-tab='tab-proximity']")
        time.sleep(1.0)
        page.select_option("#select-prox-pair", "metformin_t2d")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "08_proximity_metformin_t2d.png"))

        # 9. Disease Proximity Tab - Imatinib -> CML
        print("Capturing Disease Proximity Tab (Imatinib -> CML)...")
        page.select_option("#select-prox-pair", "imatinib_cml")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "09_proximity_imatinib_cml.png"))

        # 10. GNN Link Predictions Tab - Metformin
        print("Capturing GNN Link Predictions Tab (Metformin)...")
        page.click("button[data-tab='tab-gnn']")
        time.sleep(1.0)
        page.click("#gnn-drug-pills button[data-gdrug='metformin']")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "10_gnn_metformin.png"))

        # 11. GNN Link Predictions Tab - Imatinib
        print("Capturing GNN Link Predictions Tab (Imatinib)...")
        page.click("#gnn-drug-pills button[data-gdrug='imatinib']")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "11_gnn_imatinib.png"))

        # 12. Two-Drug Comparison Tab
        print("Capturing Two-Drug Comparison Tab...")
        page.click("button[data-tab='tab-comparison']")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "12_two_drug_comparison.png"))

        browser.close()
        print("All high-res screenshots captured successfully in:", OUT_DIR)

if __name__ == "__main__":
    capture_all()
