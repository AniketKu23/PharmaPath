"""PharmaPath Streamlit Page 2: Pathways.

Over-Representation Analysis (ORA) in KEGG & Reactome and Biological Sanity Audit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from PIL import Image
import streamlit as st

from app.ui.layout import init_page, render_filter_expander, render_responsive_dataframe
from app.ui.styles import render_back_to_top

tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

init_page("Pathways", "📊")

st.title("📊 Pathway Enrichment & Biological Sanity Audit")
st.markdown("""
Systematic Over-Representation Analysis (ORA) across **KEGG 2021 Human** and **Reactome 2022** databases  
benchmarking drug-perturbed subnetwork modules and LINCS L1000 chemical perturbation signatures.
""")

# Persistent Filters Expander (mobile and desktop accessible)
with render_filter_expander("⚙️ Enrichment Filters & Scope", "Configure drug, subnetwork scope & FDR threshold"):
    col1, col2 = st.columns(2)
    with col1:
        drug_choice = st.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0, key="pw_drug")
        drug_id = drug_choice.lower()
        scope_choice = st.radio(
            "Enrichment Scope:",
            [
                ("rwr_subnetwork", "RWR Subnetwork (Top 150)"),
                ("2hop_subnetwork", "2-Hop Subnetwork (Top 500)"),
                ("lincs_perturbed", "LINCS L1000 Perturbed Genes"),
            ],
            format_func=lambda x: x[1],
            key="pw_scope",
        )[0]
    with col2:
        fdr_thresh = st.slider("Adjusted P-Value (FDR) Threshold:", min_value=0.001, max_value=0.10, value=0.05, step=0.005, key="pw_fdr")
        db_filter = st.multiselect("Pathway Databases:", ["Reactome_2022", "KEGG_2021_Human"], default=["Reactome_2022", "KEGG_2021_Human"], key="pw_db")

# Biological Sanity Check Card
audit_json_path = tables_dir / "pathway_sanity_audit.json"
if audit_json_path.exists():
    with open(audit_json_path, "r", encoding="utf-8") as f:
        sanity_data = json.load(f)
    drug_key = "Metformin" if drug_id == "metformin" else "Imatinib"
    drug_audit = sanity_data.get(drug_key, {})
    rwr_sanity = drug_audit.get("rwr_sanity", {})

    st.subheader(f"Biological Sanity Audit: {drug_choice}")
    if rwr_sanity.get("passed", False):
        st.success(f"**Canonical Sanity Check: PASSED** — {rwr_sanity.get('verdict', '')}")
    else:
        st.warning(f"**Canonical Sanity Check**: {rwr_sanity.get('verdict', 'Investigating hallmarks.')}")

    with st.expander("🔍 Inspect Hallmarks & Matched Pathways", expanded=False):
        matched = rwr_sanity.get("matched_hallmarks", [])
        for m in matched:
            st.markdown(f"- **{m['keyword']}**: Matched *{', '.join(m['matched_terms'])}*")
        missing = rwr_sanity.get("missing_hallmarks", [])
        if missing:
            st.markdown(f"- *Missing Hallmarks*: {', '.join(missing)}")

st.markdown("---")

# Display Publication Figure
st.subheader("Publication-Quality Enrichment Dot Plot")
fig_path = figures_dir / f"pathways_{drug_id}_{scope_choice}.png"
if fig_path.exists():
    img = Image.open(fig_path)
    st.image(img, caption=f"Top Significant Pathways for {drug_choice} ({scope_choice})", width=None)
else:
    st.info("Figure not found for the selected scope.")

st.markdown("---")

# Interactive Pathway Table
st.subheader("Interactive Enriched Pathways Table")
csv_path = tables_dir / f"pathways_{drug_id}_{scope_choice}.csv"
if csv_path.exists():
    df_path = pd.read_csv(csv_path)

    col_rename = {
        "Library": "library", "Term": "term", "adj_p_value": "adj_p_value",
        "Overlap": "overlap", "odds_ratio": "odds_ratio", "combined_score": "combined_score",
        "genes": "genes"
    }
    df_path = df_path.rename(columns=col_rename)

    if "library" in df_path.columns and db_filter:
        df_path = df_path[df_path["library"].isin(db_filter)]

    if "adj_p_value" in df_path.columns:
        df_filtered = df_path[df_path["adj_p_value"] <= fdr_thresh].sort_values(by="adj_p_value")
    else:
        df_filtered = df_path

    st.write(f"Showing **{len(df_filtered)}** pathways passing FDR $\\le {fdr_thresh}$:")

    key_pw_cols = ["term", "library", "adj_p_value", "overlap", "odds_ratio"]
    render_responsive_dataframe(
        df_filtered,
        key_columns=key_pw_cols,
        download_filename=f"pathways_{drug_id}_{scope_choice}.csv",
        key_prefix="pw_data",
    )
else:
    st.info(f"Pathway table {csv_path.name} not found.")

render_back_to_top()
