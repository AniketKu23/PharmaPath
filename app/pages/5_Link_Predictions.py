"""PharmaPath Streamlit Page 5: Link Predictions.

Inductive GNN Link Prediction, Leave-Targets-Out Recovery, and Top-20 Novel Drug-Protein Hypotheses.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

st.set_page_config(page_title="Link Predictions | PharmaPath", page_icon="🤖", layout="wide")

st.title("🤖 Graph Neural Network Link Prediction & Target Recovery")
st.markdown("""
Inductive Graph Neural Network (GNN) link prediction on the human PPI interactome scaffold:
- **GraphSAGE**: 2-layer mean-aggregation inductive message passing.
- **Graph Autoencoder (GAE)**: Non-linear spectral node encoder with dot-product edge decoder.
- **Strict Leakage Prevention**: Split performed via PyG `RandomLinkSplit`. Zero test edges are utilized in message-passing or embedding construction.
""")

st.markdown("---")

# 1. PPI Link Prediction Metrics
st.subheader("1. PPI Scaffold Link Prediction Benchmark")
gnn_metrics_file = tables_dir / "gnn_ppi_link_prediction_metrics.csv"
if gnn_metrics_file.exists():
    df_metrics = pd.read_csv(gnn_metrics_file)
    st.dataframe(
        df_metrics,
        column_config={
            "Model": st.column_config.TextColumn("Model Architecture"),
            "Test AUROC": st.column_config.NumberColumn("Test AUROC", format="%.4f"),
            "Test Average Precision": st.column_config.NumberColumn("Test Average Precision (AP)", format="%.4f"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.error("GNN metrics file not found.")

roc_pr_img = figures_dir / "gnn_link_prediction_roc_pr.png"
if roc_pr_img.exists():
    img = Image.open(roc_pr_img)
    st.image(img, caption="Test Split ROC and Precision-Recall Curves (Zero Data Leakage)", use_column_width=True)

st.markdown("---")

# 2. Leave-Targets-Out Validation
st.subheader("2. Drug Target Recovery Benchmark (Leave-Targets-Out)")
st.markdown("""
A subset of known primary drug targets is hidden during embedding inference.  
The model ranks all 15,882 human proteins by cosine similarity to the drug node embedding to evaluate target recovery without leakage.
""")

rec_file = tables_dir / "leave_targets_out_metrics.csv"
if rec_file.exists():
    df_rec = pd.read_csv(rec_file)
    st.dataframe(df_rec, use_container_width=True, hide_index=True)

st.markdown("---")

# 3. Top-20 Novel Drug-Protein Hypotheses & Literature Verification
st.subheader("3. Predicted Novel Drug-Protein Hypotheses (Top 20)")

st.warning("""
⚠️ **Methodological Caveat**: Computational predictions represent proteins topologically and functionally coupled to the drug target subnetwork in the interactome.  
They are **computational hypotheses** for drug repurposing or off-target interaction, **not** experimental proof of direct biochemical binding.
""")

drug_choice = st.selectbox("Select Drug to Inspect Hypotheses:", ["Metformin", "Imatinib"])
drug_id = drug_choice.lower()

hyp_file = tables_dir / f"top20_hypotheses_{drug_id}.csv"
lit_file = tables_dir / "literature_check_table.csv"

if hyp_file.exists():
    df_hyp = pd.read_csv(hyp_file)

    # Merge literature table details if available
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

    st.dataframe(
        merged_df,
        column_config={
            "rank": st.column_config.NumberColumn("Rank"),
            "candidate_protein": st.column_config.TextColumn("Candidate Protein"),
            "confidence_score": st.column_config.NumberColumn("Confidence Score", format="%.4f"),
            "status": st.column_config.TextColumn("Status"),
            "PubMed Search Link": st.column_config.LinkColumn("PubMed Query", display_text="Search PubMed"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(f"Hypotheses file for {drug_choice} not found.")
