"""PharmaPath Streamlit Page 5: Link Predictions.

Inductive GNN Link Prediction, Leave-Targets-Out Recovery, and Top-20 Novel Drug-Protein Hypotheses.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from PIL import Image
import streamlit as st

from app.ui.layout import init_page, render_responsive_dataframe
from app.ui.styles import render_back_to_top

tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

init_page("Link Predictions", "🤖")

st.title("🤖 Graph Neural Network Link Prediction & Target Recovery")
st.markdown("""
Inductive Graph Neural Network (GNN) link prediction on the human PPI interactome scaffold:
- **GraphSAGE**: 2-layer mean-aggregation inductive message passing.
- **Graph Autoencoder (GAE)**: Non-linear spectral node encoder with dot-product edge decoder.
- **Strict Leakage Prevention**: Split performed via PyG `RandomLinkSplit`. Zero test edges are utilized in message-passing or embedding construction.
""")

with st.expander("💡 Concept Guide: Inductive GNNs, Leakage Prevention & Target Recovery", expanded=False):
    st.markdown("""
    - **Inductive Message Passing (GraphSAGE)**: Learns neighborhood aggregation functions rather than static node embeddings. Can generalize inductively to unseen nodes and edges without retraining.
    - **Zero Data Leakage Protocol**: Using PyTorch Geometric `RandomLinkSplit`, test edges are strictly quarantined. Test links are never present in the computation graph during message passing.
    - **Leave-Targets-Out Cross-Validation**: True known drug targets are masked during inference. The GNN ranks all 15,882 human proteins by cosine similarity to determine target recovery rates (Hits@10, Hits@20, Hits@50).
    - **Off-Target & Repurposing Hypotheses**: High-confidence predicted links represent proteins topologically and functionally coupled to the drug target subnetwork.
    """)

st.markdown("---")

tab_bench, tab_recovery, tab_hypotheses = st.tabs([
    "📊 GNN Benchmark",
    "🎯 Target Recovery",
    "💡 Top-20 Hypotheses & Evidence",
])

with tab_bench:
    st.subheader("1. PPI Scaffold Link Prediction Benchmark")
    gnn_metrics_file = tables_dir / "gnn_ppi_link_prediction_metrics.csv"
    if gnn_metrics_file.exists():
        df_metrics = pd.read_csv(gnn_metrics_file)
        render_responsive_dataframe(
            df_metrics,
            key_columns=["Model", "Test AUROC", "Test Average Precision"],
            download_filename="gnn_benchmark_metrics.csv",
            key_prefix="gnn_bench",
        )
    else:
        st.error("GNN metrics file not found.")

    roc_pr_img = figures_dir / "gnn_link_prediction_roc_pr.png"
    if roc_pr_img.exists():
        img = Image.open(roc_pr_img)
        st.image(img, caption="Test Split ROC and Precision-Recall Curves (Zero Data Leakage)", width=None)

with tab_recovery:
    st.subheader("2. Drug Target Recovery Benchmark (Leave-Targets-Out)")
    st.markdown("""
    A subset of known primary drug targets is hidden during embedding inference.  
    The model ranks all 15,882 human proteins by cosine similarity to evaluate target recovery without leakage.
    """)
    rec_file = tables_dir / "leave_targets_out_metrics.csv"
    if rec_file.exists():
        df_rec = pd.read_csv(rec_file)
        render_responsive_dataframe(
            df_rec,
            download_filename="leave_targets_out_metrics.csv",
            key_prefix="gnn_recovery",
        )

with tab_hypotheses:
    st.subheader("3. Predicted Novel Drug-Protein Hypotheses (Top 20)")
    st.warning("""
    ⚠️ **Methodological Caveat**: Computational predictions represent proteins topologically and functionally coupled to the drug target subnetwork in the interactome.  
    They are **computational hypotheses** for drug repurposing or off-target interaction, **not** experimental proof of direct biochemical binding.
    """)

    drug_choice = st.selectbox("Select Drug to Inspect Hypotheses:", ["Metformin", "Imatinib"], key="gnn_drug_sel")
    drug_id = drug_choice.lower()

    hyp_file = tables_dir / f"top20_hypotheses_{drug_id}.csv"
    lit_file = tables_dir / "literature_check_table.csv"

    if hyp_file.exists():
        df_hyp = pd.read_csv(hyp_file)

        if lit_file.exists():
            df_lit = pd.read_csv(lit_file)
            sub_lit = df_lit[df_lit["Drug"].str.lower() == drug_id]
            merged_df = pd.merge(
                df_hyp,
                sub_lit[["Candidate Protein", "Biological Interactome Context", "Literature Cross-Check Status", "PubMed Search Link"]],
                left_on="candidate_protein",
                right_on="Candidate Protein",
                how="left",
            )
        else:
            merged_df = df_hyp

        key_hyp_cols = ["rank", "candidate_protein", "confidence_score", "status", "Literature Cross-Check Status"]
        render_responsive_dataframe(
            merged_df,
            key_columns=[c for c in key_hyp_cols if c in merged_df.columns],
            download_filename=f"top20_hypotheses_{drug_id}.csv",
            key_prefix="gnn_hyp_table",
        )
    else:
        st.info(f"Hypotheses file for {drug_choice} not found.")

render_back_to_top()
