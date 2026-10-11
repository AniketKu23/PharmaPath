"""PharmaPath Streamlit Page 2: Pathways.

Over-Representation Analysis (ORA) in KEGG & Reactome and Biological Sanity Audit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
tables_dir = ROOT_DIR / "results" / "tables"
figures_dir = ROOT_DIR / "results" / "figures"

st.set_page_config(page_title="Pathways | PharmaPath", page_icon="📊", layout="wide")

st.title("📊 Pathway Enrichment & Biological Sanity Audit")
st.markdown("""
Systematic Over-Representation Analysis (ORA) across **KEGG 2021 Human** and **Reactome 2022** databases  
benchmarking drug-perturbed subnetwork modules and LINCS L1000 chemical perturbation signatures.
""")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.sidebar.header("Enrichment Filters")
    drug_choice = st.sidebar.selectbox("Select Drug:", ["Metformin", "Imatinib"], index=0)
    drug_id = drug_choice.lower()

    scope_choice = st.sidebar.radio(
        "Enrichment Scope:",
        [
            ("rwr_subnetwork", "RWR Subnetwork (Top 150)"),
            ("2hop_subnetwork", "2-Hop Subnetwork (Top 500)"),
            ("lincs_perturbed", "LINCS L1000 Perturbed Genes"),
        ],
        format_func=lambda x: x[1],
    )[0]

    fdr_thresh = st.sidebar.slider("Adjusted P-Value (FDR) Threshold:", min_value=0.001, max_value=0.10, value=0.05, step=0.005)
    db_filter = st.sidebar.multiselect("Pathway Databases:", ["Reactome_2022", "KEGG_2021_Human"], default=["Reactome_2022", "KEGG_2021_Human"])

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

    with st.expander("Inspect Hallmarks & Matched Pathways"):
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
    st.image(img, caption=f"Top Significant Pathways for {drug_choice} ({scope_choice})", use_column_width=True)
else:
    st.info("Figure not found for the selected scope.")

st.markdown("---")

# Interactive Pathway Table
st.subheader("Interactive Enriched Pathways Table")
csv_path = tables_dir / f"pathways_{drug_id}_{scope_choice}.csv"
if csv_path.exists():
    df_path = pd.read_csv(csv_path)

    # Standardize column naming
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

    st.dataframe(
        df_filtered,
        column_config={
            "adj_p_value": st.column_config.NumberColumn("Adjusted P-Value", format="%.2e"),
            "odds_ratio": st.column_config.NumberColumn("Odds Ratio", format="%.2f"),
            "combined_score": st.column_config.NumberColumn("Combined Score", format="%.2f"),
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(f"Pathway table {csv_path.name} not found.")
