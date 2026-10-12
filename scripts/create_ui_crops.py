"""Generate focused high-resolution crops of specific interactive components for the presentation slides."""

from pathlib import Path
from PIL import Image

ASSETS_DIR = Path("reports/ppt_assets")
CROPS_DIR = ASSETS_DIR / "crops"
CROPS_DIR.mkdir(parents=True, exist_ok=True)

def create_crops():
    # 1. Metformin Canvas Viewport (x: 800 to 2800, y: 150 to 1550)
    img1 = Image.open(ASSETS_DIR / "01_subnetwork_metformin.png")
    w, h = img1.size  # 2880, 1620
    crop_canvas_met = img1.crop((int(w * 0.27), int(h * 0.08), int(w * 0.98), int(h * 0.95)))
    crop_canvas_met.save(CROPS_DIR / "crop_canvas_metformin.png")
    print("Saved crop_canvas_metformin.png")

    # 2. Imatinib Canvas Viewport
    img2 = Image.open(ASSETS_DIR / "02_subnetwork_imatinib.png")
    crop_canvas_ima = img2.crop((int(w * 0.27), int(h * 0.08), int(w * 0.98), int(h * 0.95)))
    crop_canvas_ima.save(CROPS_DIR / "crop_canvas_imatinib.png")
    print("Saved crop_canvas_imatinib.png")

    # 3. Pathways Charts & Tables (Metformin)
    img4 = Image.open(ASSETS_DIR / "04_pathways_metformin.png")
    crop_pathways = img4.crop((int(w * 0.50), int(h * 0.08), int(w * 0.98), int(h * 0.95)))
    crop_pathways.save(CROPS_DIR / "crop_pathways_metformin.png")
    print("Saved crop_pathways_metformin.png")

    # 4. Centrality Scatter & Modularity
    img7 = Image.open(ASSETS_DIR / "07_centralities_imatinib.png")
    crop_cent_scatter = img7.crop((int(w * 0.02), int(h * 0.12), int(w * 0.49), int(h * 0.92)))
    crop_cent_scatter.save(CROPS_DIR / "crop_centrality_scatter.png")
    crop_cent_clusters = img7.crop((int(w * 0.51), int(h * 0.12), int(w * 0.98), int(h * 0.92)))
    crop_cent_clusters.save(CROPS_DIR / "crop_centrality_clusters.png")
    print("Saved crop_centrality_scatter.png and crop_centrality_clusters.png")

    # 5. Disease Proximity (Metformin -> T2D)
    img8 = Image.open(ASSETS_DIR / "08_proximity_metformin_t2d.png")
    crop_prox_met = img8.crop((int(w * 0.02), int(h * 0.12), int(w * 0.49), int(h * 0.92)))
    crop_prox_met.save(CROPS_DIR / "crop_proximity_chart_met.png")
    crop_prox_summary = img8.crop((int(w * 0.51), int(h * 0.12), int(w * 0.98), int(h * 0.92)))
    crop_prox_summary.save(CROPS_DIR / "crop_proximity_summary.png")
    print("Saved crop_proximity_chart_met.png and crop_proximity_summary.png")

    # 6. GNN Link Predictions
    img10 = Image.open(ASSETS_DIR / "10_gnn_metformin.png")
    crop_gnn_benchmark = img10.crop((int(w * 0.02), int(h * 0.12), int(w * 0.49), int(h * 0.92)))
    crop_gnn_benchmark.save(CROPS_DIR / "crop_gnn_benchmark.png")
    crop_gnn_hypotheses = img10.crop((int(w * 0.51), int(h * 0.12), int(w * 0.98), int(h * 0.92)))
    crop_gnn_hypotheses.save(CROPS_DIR / "crop_gnn_hypotheses.png")
    print("Saved crop_gnn_benchmark.png and crop_gnn_hypotheses.png")

    # 7. Two-Drug Comparison
    img12 = Image.open(ASSETS_DIR / "12_two_drug_comparison.png")
    crop_comp_left = img12.crop((int(w * 0.02), int(h * 0.12), int(w * 0.49), int(h * 0.95)))
    crop_comp_left.save(CROPS_DIR / "crop_comparison_menche.png")
    crop_comp_right = img12.crop((int(w * 0.51), int(h * 0.12), int(w * 0.98), int(h * 0.95)))
    crop_comp_right.save(CROPS_DIR / "crop_comparison_synergy.png")
    print("Saved crop_comparison_menche.png and crop_comparison_synergy.png")

if __name__ == "__main__":
    create_crops()
