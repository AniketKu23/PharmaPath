"""PharmaPath: Interactive Network-Pharmacology & GNN Discovery Platform.

Home / Overview Page.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root and src to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from app.ui.layout import init_page, render_responsive_dataframe
from app.ui.styles import render_ascii_box, render_back_to_top, render_metric_grid

# Initialize responsive layout and styles
init_page("Overview", "🧬")

st.title("🧬 PharmaPath: Network-Pharmacology & GNN Discovery Pipeline")
st.markdown("""
**An end-to-end multi-omics network pharmacology framework and Graph Neural Network pipeline.**  
PharmaPath investigates how multi-target metabolic drugs (**Metformin**) and targeted kinase inhibitors (**Imatinib**) perturb the human Protein-Protein Interaction (PPI) interactome scaffold across distinct disease contexts (**Type 2 Diabetes** and **Chronic Myeloid Leukemia**).
""")

st.markdown("---")

# Key Metrics Dashboard (Responsive 2x2 grid on mobile, 4x1 on desktop)
metrics_data = [
    {
        "label": "Human PPI LCC Nodes",
        "value": "15,882",
        "delta": "STRING v12 (Score ≥ 700)",
    },
    {
        "label": "High-Confidence Edges",
        "value": "236,712",
        "delta": "Undirected Density = 0.0019",
    },
    {
        "label": "GNN Link Test AUROC",
        "value": "0.8865",
        "delta": "GraphSAGE Inductive (No Leakage)",
    },
    {
        "label": "Disease Proximity (Z-Score)",
        "value": "-18.28",
        "delta": "Metformin → T2D (p = 0.001)",
    },
]
render_metric_grid(metrics_data)

st.markdown("---")

# Architectural Workflow
st.subheader("System Architecture & Multi-Omics Workflow")
col_arch, col_info = st.columns([3, 2])

with col_arch:
    ascii_flow = """┌────────────────────────────────────────────────────────────────────────┐
│                      1. Multi-Omics Data Ingestion                     │
│   STRING v12 PPI (Score≥700) • ChEMBL / Seed Targets • LINCS L1000     │
│           Open Targets Platform GraphQL (T2D & CML Disease Genes)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   2. Topological Scaffold & Subnetworks                │
│    15,882-Node PPI LCC • 2-Hop Neighborhood • Random Walk with Restart │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              3. Expression Overlay & Pathway Enrichment (ORA)          │
│    Enrichr KEGG 2021 & Reactome 2022 • Biological Sanity Hallmarks     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│         4. Network Topology & Disease Module Proximity (d_c)           │
│  Centrality Hubs/Bottlenecks • Louvain Modularity • Guney 1000x Perms │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            5. Graph Neural Network (GNN) Link Prediction & Recovery    │
│   GraphSAGE (AUROC 0.8865) • GAE (0.8832) • Leave-Targets-Out Cross-Val│
│             Top-20 Computational Hypotheses & Literature Audit         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│          6. Two-Drug Comparative Network Pharmacology (Menche s_AB)    │
│       Metformin + Imatinib Combination Synergy & Cross-Talk Hubs       │
└────────────────────────────────────────────────────────────────────────┘"""
    render_ascii_box(ascii_flow)

with col_info:
    st.markdown("### The Two Case Study Drugs")
    st.markdown("""
    - **Metformin** *(Indirect, Multi-Target Metabolic Regulator)*:
      - **Seed Targets**: `PRKAA1`, `PRKAA2`, `PRKAB1`, `PRKAG1`, `GPD2`, plus mitochondrial complex I subunits (`NDUF*` genes) in interactome scaffold (61 targets mapped to LCC).
      - **Disease Scaffolding**: **Type 2 Diabetes** (Open Targets GraphQL: 500 genes).
      - **Mechanism**: Modulates cellular energy homeostasis, activates AMPK, inhibits mTORC1 and gluconeogenesis.
    
    - **Imatinib** *(Targeted Tyrosine Kinase Inhibitor - Ground Truth)*:
      - **Seed Targets**: `ABL1`, `BCR`, `KIT`, `PDGFRA`, `PDGFRB`, `CSF1R`, `DDR1`, `NQO2` (10 targets mapped to LCC).
      - **Disease Scaffolding**: **Chronic Myeloid Leukemia (CML)** (Open Targets GraphQL: 162 genes).
      - **Mechanism**: Competitively inhibits ATP binding site of BCR-ABL oncoprotein tyrosine kinase.
    """)

st.markdown("---")

# Pipeline Validation Audit Table
st.subheader("Automated Quality Assurance & Pillar Verification")
summary_csv = ROOT_DIR / "results" / "tables" / "pipeline_validation_summary.csv"
if summary_csv.exists():
    val_df = pd.read_csv(summary_csv)
    key_cols = [c for c in ["module", "status", "metric", "value"] if c in val_df.columns]
    render_responsive_dataframe(
        val_df,
        key_columns=key_cols if len(key_cols) >= 3 else None,
        download_filename="pipeline_validation_summary.csv",
        key_prefix="overview_val",
    )
else:
    st.info("Run `python scripts/run_all.py` to generate complete validation metrics.")

st.markdown("---")
st.markdown("""
### Explore PharmaPath Pages:
- 🔭 **Drug Explorer**: Interactive PyVis subnetwork graphs with expression overlay, centrality sizing, and filters.
- 📊 **Pathways**: Over-representation analysis (ORA) in KEGG & Reactome with biological sanity audit.
- 🕸️ **Network Metrics**: Hub and bottleneck identification, Louvain community modularity, and dominant pathways.
- 🎯 **Disease Proximity**: Guney et al. (2016) closest-distance metric $d_c$ with 1,000 degree-matched null permutations.
- 🤖 **Link Predictions**: Inductive GraphSAGE & GAE benchmark, leave-targets-out recovery, and top-20 hypotheses with PubMed links.
- ⚖️ **Drug Comparison**: Menche et al. (2015) separation $s_{AB}$, cross-talk hubs, and combination therapy rationale.
""")

render_back_to_top()
