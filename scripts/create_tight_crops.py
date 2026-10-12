"""Generate tight, perfectly framed crops of UI components to eliminate empty black bars."""

from pathlib import Path
from PIL import Image

ASSETS_DIR = Path("reports/ppt_assets")
CROPS_DIR = ASSETS_DIR / "crops"
CROPS_DIR.mkdir(parents=True, exist_ok=True)

def generate_tight_crops():
    # 1. Protein Modal tight crop (from 03_protein_modal.png)
    # The modal is in the middle of a 2880 x 1620 screen
    im_modal = Image.open(ASSETS_DIR / "03_protein_modal.png")
    w, h = im_modal.size  # 2880, 1620
    # modal card is roughly center x: 900 to 1980, y: 450 to 1180
    crop_modal = im_modal.crop((int(w * 0.32), int(h * 0.28), int(w * 0.68), int(h * 0.74)))
    crop_modal.save(CROPS_DIR / "tight_protein_modal.png")
    print("Saved tight_protein_modal.png")

    # 2. Subnetwork Canvas Viewport (from 01_subnetwork_metformin.png)
    im_net = Image.open(ASSETS_DIR / "01_subnetwork_metformin.png")
    crop_net = im_net.crop((int(w * 0.26), int(h * 0.14), int(w * 0.98), int(h * 0.97)))
    crop_net.save(CROPS_DIR / "tight_subnetwork_canvas.png")
    print("Saved tight_subnetwork_canvas.png")

    # 3. Pathways Studio (from 05_pathways_imatinib.png)
    im_path = Image.open(ASSETS_DIR / "05_pathways_imatinib.png")
    crop_path = im_path.crop((int(w * 0.02), int(h * 0.13), int(w * 0.98), int(h * 0.90)))
    crop_path.save(CROPS_DIR / "tight_pathways_studio.png")
    print("Saved tight_pathways_studio.png")

    # 4. Centrality Studio (from 07_centralities_imatinib.png)
    im_cent = Image.open(ASSETS_DIR / "07_centralities_imatinib.png")
    crop_cent = im_cent.crop((int(w * 0.02), int(h * 0.13), int(w * 0.98), int(h * 0.90)))
    crop_cent.save(CROPS_DIR / "tight_centrality_studio.png")
    print("Saved tight_centrality_studio.png")

    # 5. Disease Proximity Studio (from 09_proximity_imatinib_cml.png)
    im_prox = Image.open(ASSETS_DIR / "09_proximity_imatinib_cml.png")
    crop_prox = im_prox.crop((int(w * 0.02), int(h * 0.13), int(w * 0.98), int(h * 0.92)))
    crop_prox.save(CROPS_DIR / "tight_proximity_studio.png")
    print("Saved tight_proximity_studio.png")

    # 6. GNN Studio (from 11_gnn_imatinib.png)
    im_gnn = Image.open(ASSETS_DIR / "11_gnn_imatinib.png")
    crop_gnn = im_gnn.crop((int(w * 0.02), int(h * 0.13), int(w * 0.98), int(h * 0.92)))
    crop_gnn.save(CROPS_DIR / "tight_gnn_studio.png")
    print("Saved tight_gnn_studio.png")

    # 7. Two-Drug Comparison Studio (from 12_two_drug_comparison.png)
    im_comp = Image.open(ASSETS_DIR / "12_two_drug_comparison.png")
    crop_comp = im_comp.crop((int(w * 0.02), int(h * 0.13), int(w * 0.98), int(h * 0.92)))
    crop_comp.save(CROPS_DIR / "tight_comparison_studio.png")
    print("Saved tight_comparison_studio.png")

if __name__ == "__main__":
    generate_tight_crops()
