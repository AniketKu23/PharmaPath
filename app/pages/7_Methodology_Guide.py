"""PharmaPath Streamlit Page 7: Methodology & Concept Guide.

Exhaustive interactive glossary and scientific explanation of all algorithms,
topological metrics, multi-omics overlays, and GNN models used in PharmaPath.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.ui.layout import init_page
from app.ui.styles import render_back_to_top

init_page("Methodology Guide", "📖")

st.title("📖 PharmaPath: Concepts & Methodology Guide")
st.markdown("""
Welcome to the **PharmaPath Scientific & Algorithmic Knowledge Base**.  
This guide explains every algorithm, topological metric, multi-omics overlay, and machine learning technique implemented in the pipeline.
""")

st.markdown("---")

# Navigation Tabs
tab_sub, tab_topo, tab_prox, tab_gnn, tab_comp = st.tabs([
    "🕸️ 1. Subnetwork Extraction",
    "📊 2. Interactome Topology & Centrality",
    "🎯 3. Disease Proximity (Guney)",
    "🤖 4. Inductive GNN Link Prediction",
    "⚖️ 5. Comparative Pharmacology (Menche)",
])

# ==============================================================================
# TAB 1: Subnetwork Extraction & Expression Overlay
# ==============================================================================
with tab_sub:
    st.header("1. Subnetwork Extraction Algorithms & Expression Overlay")

    st.subheader("Random Walk with Restart (RWR)")
    st.markdown("""
    **What is it?**  
    Random Walk with Restart (RWR) is a global network diffusion algorithm that simulates an imaginary random walker traversing the human Protein-Protein Interaction (PPI) graph.
    
    **How it works mathematically:**  
    - The walker begins at the drug's **seed target proteins** (defined by initial probability vector $\\mathbf{p}_0$).
    - At every discrete step $t$, the walker transitions to an adjacent protein proportional to edge confidence scores with probability $1 - r$.
    - With restart probability $r$ (configured at $r = 0.5$), the walker jumps back to the seed target nodes:
    
    $$\\mathbf{p}_{t+1} = (1 - r) \\mathbf{W} \\mathbf{p}_t + r \\mathbf{p}_0$$
    
    where $\\mathbf{W}$ is the column-normalized adjacency/transition matrix of the PPI interactome.  
    - The system iterates until stationary convergence ($||\\mathbf{p}_{t+1} - \\mathbf{p}_t||_1 < 10^{-6}$).
    
    **Why do we use it?**  
    RWR measures **global topological affinity**. Unlike simple path searches, RWR captures multi-pathway diffusion and prioritizes proteins that have *multiple reinforcing pathways* connecting back to drug targets, filtering out isolated dead-ends. We extract the **top 150 proteins** by steady-state probability $\\mathbf{p}_\\infty$.
    """)

    st.markdown("---")
    st.subheader("2-Hop Interactome Neighborhood")
    st.markdown("""
    **What is it?**  
    The 2-hop neighborhood extracts all direct physical interactors (1-hop neighbors) of the drug targets, plus all interactors of those neighbors (2-hop neighbors).
    
    **Biological rationale:**  
    - **1-Hop Neighbors**: Direct biological effectors, kinase substrates, scaffolding partners, and primary signaling complexes.
    - **2-Hop Neighbors**: Secondary downstream effectors, transcription factor cascades, and pathway feedback loops.
    
    **RWR vs. 2-Hop Tradeoffs:**
    | Dimension | Random Walk with Restart (RWR) | 2-Hop Neighborhood |
    | :--- | :--- | :--- |
    | **Scope** | Global diffusion across entire interactome | Strictly local distance-bounded radius ($d \\le 2$) |
    | **Target Prioritization** | Weights nodes by multi-path convergence | Treats all 1-hop and 2-hop edges equally |
    | **Hub Susceptibility** | Resilient against hub explosion | Can expand rapidly if seed targets include major hubs |
    | **Module Size** | Top 150 nodes (densely connected core) | Pruned to Top 500 nodes by degree |
    """)

    st.markdown("---")
    st.subheader("Node Color & Visual Coding")
    st.markdown("""
    In the **Drug Explorer** interactive canvas:
    - 🌟 **Gold Star**: **Seed Drug Target** (experimentally validated binding target from ChEMBL/DGIdb).
    - 🔴 **Crimson / Red ($z > +1.0$)**: **Up-regulated gene** in LINCS L1000 chemical perturbation signatures (compensatory pathway activation or transcriptional induction).
    - 🟢 **Emerald / Green ($z < -1.0$)**: **Down-regulated gene** in LINCS L1000 chemical perturbation signatures (transcriptional repression or pathway shutdown).
    - 🔵 **Steel Blue**: **Interactome Scaffold Neighbor** (structural PPI bridge connecting active signaling cascades).
    - **Node Diameter**: Scaled dynamically by topological centrality (degree, betweenness, or eigenvector).
    """)

# ==============================================================================
# TAB 2: Topology & Centralities
# ==============================================================================
with tab_topo:
    st.header("2. Interactome Topology, Centralities & Modularity")

    st.markdown("""
    Biological networks are **scale-free** ($P(k) \\sim k^{-\\gamma}$) and display **small-world** properties: most proteins have few connections, while a small elite set of proteins serve as high-degree communication backbones.
    """)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("Topological Centrality Measures")
        st.markdown("""
        1. **Degree Centrality ($k_v$)**:
           - Number of direct physical interactions a protein maintains.
           - Identifies **Structural Hubs** (e.g. master scaffolding complexes).
        
        2. **Betweenness Centrality ($C_B(v)$)**:
           - Fraction of all shortest paths in the interactome passing through protein $v$:
           $$C_B(v) = \\sum_{s \\neq v \\neq t} \\frac{\\sigma_{st}(v)}{\\sigma_{st}}$$
           - Identifies **Bottlenecks**: chokepoints controlling communication between functional modules.
        
        3. **Eigenvector Centrality ($x_v$)**:
           - Measures influence: a protein scores highly if it connects to other high-scoring proteins:
           $$\\lambda x_v = \\sum_{u \\in \\mathcal{N}(v)} x_u$$
        
        4. **Closeness Centrality ($C_C(v)$)**:
           - Reciprocal of average shortest distance to all other proteins:
           $$C_C(v) = \\frac{N - 1}{\\sum_{u \\neq v} d(v, u)}$$
        """)

    with col_t2:
        st.subheader("Topological Role Classification")
        st.markdown("""
        - **Topological Hub (Top 5% Degree)**:
          - High connectivity. Essential proteins whose genetic disruption frequently causes lethality (*centrality-lethality rule*).
        
        - **Bottleneck (Top 5% Betweenness)**:
          - High information flow. Often dynamic signaling bridges, transcription factors, or key mediators of **drug resistance**.
        
        - **Dual Hub-Bottleneck Bridge**:
          - Rare proteins sitting in both the top 5% of degree and top 5% of betweenness (e.g., `SRC`, `MAPK1`, `TP53`, `STAT3`).
          - Critical therapeutic anchors controlling cellular fate.
        
        - **Louvain Community Detection & Modularity ($Q$)**:
          - Unsupervised greedy optimization of modularity $Q$ partitioning the subnetwork into dense functional clusters.
          - Each community is systematically audited via Over-Representation Analysis (ORA) to identify its dominant KEGG/Reactome pathway.
        """)

# ==============================================================================
# TAB 3: Disease Proximity
# ==============================================================================
with tab_prox:
    st.header("3. Disease Module Network Proximity (Guney et al., 2016)")

    st.markdown("""
    According to the **disease module hypothesis** (Barabási et al., *Nature Reviews Genetics* 2011), proteins associated with a specific complex disease do not scatter randomly across the interactome; they form a localized subnetwork module.  
    To determine if a drug treats a disease, we quantify whether the drug's targets $T$ are topologically closer to the disease gene set $S$ than expected by chance.
    """)

    st.subheader("Closest-Distance Metric $\\langle d_c \\rangle$")
    st.markdown("""
    Following **Guney et al. (Nature Communications 2016)**, closest distance measures the average shortest path distance from each drug target $t \\in T$ to the nearest disease gene $s \\in S$:
    
    $$\\langle d_c \\rangle = \\frac{1}{|T|} \\sum_{t \\in T} \\min_{s \\in S} d(t, s)$$
    """)

    st.subheader("Why 1,000 Degree-Matched Permutations?")
    st.markdown("""
    In scale-free networks, high-degree hubs naturally sit close to every node simply due to sheer connectivity. Evaluating proximity against uniform random nodes would introduce severe **hub bias**, falsely claiming that any drug targeting a hub treats every disease!
    
    **Methodological Solution**:
    - We bin all 15,882 interactome proteins into degree intervals (bin size = 5).
    - We draw **1,000 degree-matched pseudo-target sets** $T_{\\text{null}}$ where each node matches the exact degree of a true drug target.
    - We compute the null distribution mean $\\mu_{\\text{null}}$ and standard deviation $\\sigma_{\\text{null}}$.
    - **Z-Score Calculation**:
      $$z = \\frac{\\langle d_c \\rangle - \\mu_{\\text{null}}}{\\sigma_{\\text{null}}}$$
    - **Empirical P-Value**:
      $$p = \\frac{1}{B} \\sum_{b=1}^B \\mathbb{I}\\left(d_c^{(b)} \\le \\langle d_c \\rangle\\right)$$
    
    **Decision Threshold**:
    - $z < -2.0$ ($p < 0.05$): **Statistically Proximate** — the drug targets are concentrated inside or adjacent to the disease module.
    - $z \\ge -2.0$: **Topologically Distant / Non-Specific**.
    """)

# ==============================================================================
# TAB 4: GNN Link Prediction
# ==============================================================================
with tab_gnn:
    st.header("4. Inductive Graph Neural Networks (GNNs) & Link Prediction")

    st.markdown("""
    PharmaPath implements inductive deep graph representation learning to predict unknown protein-protein links and discover novel drug-target repurposing leads.
    """)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Model Architectures")
        st.markdown("""
        1. **GraphSAGE (Sample and Aggregate)**:
           - 2-layer inductive message passing.
           - Aggregates neighborhood representations:
           $$\\mathbf{h}_v^{(k)} = \\sigma\\left(\\mathbf{W} \\cdot [\\mathbf{h}_v^{(k-1)} \\,\\|\\, \\text{AGG}(\\{\\mathbf{h}_u^{(k-1)} : u \\in \\mathcal{N}(v)\\})]\\right)$$
           - Generates embeddings for unseen nodes/edges without retraining the full interactome.
        
        2. **Graph Autoencoder (GAE)**:
           - Encoder: 2-layer Graph Convolutional Network (GCN) producing latent matrix $\\mathbf{Z} \\in \\mathbb{R}^{N \\times d}$.
           - Decoder: Non-linear inner product reconstructing adjacency:
           $$\\hat{\\mathbf{A}} = \\sigma(\\mathbf{Z} \\mathbf{Z}^T)$$
        
        3. **Node2Vec + Logistic Regression (Baseline)**:
           - Biased random walks (parameters $p=1.0, q=1.0$) producing Skip-Gram vector embeddings classified via Logistic Regression.
        """)

    with col_g2:
        st.subheader("Strict Leakage Prevention & Validation")
        st.markdown("""
        - **Zero Data Leakage (PyG `RandomLinkSplit`)**:
          - Edges are partitioned into **Train (80%)**, **Validation (10%)**, and **Test (10%)**.
          - Test edges are completely removed from the graph during message passing and embedding construction.
        
        - **Negative Sampling**:
          - For every true positive interactome edge, an equal number of non-edges are uniformly sampled as negative training pairs.
        
        - **Leave-Targets-Out Target Recovery Benchmark**:
          - A subset of known true drug targets is hidden during inference.
          - The GNN ranks all 15,882 proteins in the human genome by cosine similarity to the drug embedding.
          - We report **Hits@10**, **Hits@20**, and **Hits@50** to measure how frequently true hidden targets appear in the top-ranked predictions without data leakage.
        """)

# ==============================================================================
# TAB 5: Comparative Pharmacology
# ==============================================================================
with tab_comp:
    st.header("5. Two-Drug Comparative Network Pharmacology (Menche et al., 2015)")

    st.markdown("""
    How do two drugs with opposing mechanisms interact in the human interactome? PharmaPath benchmarks **Metformin** (indirect metabolic regulator) against **Imatinib** (targeted oncogenic kinase inhibitor).
    """)

    st.subheader("Network Separation Metric $s_{AB}$")
    st.markdown("""
    Following **Menche et al. (Science 2015)**, the network separation $s_{AB}$ measures the topological distance between two subnetwork modules $A$ and $B$:
    
    $$s_{AB} = \\langle d_{AB} \\rangle - \\frac{\\langle d_{AA} \\rangle + \\langle d_{BB} \\rangle}{2}$$
    
    where:
    - $\\langle d_{AB} \\rangle$: Average shortest distance between proteins in module $A$ and module $B$.
    - $\\langle d_{AA} \\rangle, \\langle d_{BB} \\rangle$: Internal shortest distance within module $A$ and module $B$.
    
    **Interpretation**:
    - **$s_{AB} < 0$ (Module Overlap)**: The two drug perturbomes overlap topologically. They share downstream signaling cascades, indicating either direct target competition or strong mechanistic synergy.
    - **$s_{AB} \\ge 0$ (Module Separation)**: The two drug perturbomes occupy distinct topological neighborhoods in the human interactome. They act through independent functional channels, lowering competitive antagonism.
    """)

    st.subheader("Combination Synergy & Cross-Talk Hubs")
    st.markdown("""
    - **Shared Cross-Talk Hubs**: Proteins present in both drug subnetworks that mediate signal integration (e.g. `PRKAA1`, `mTOR`, `AKT1`, `SRC`).
    - **Clinical Combination Rationale**:
      - In Chronic Myeloid Leukemia (CML) and gastrointestinal stromal tumors, cancer cells frequently exhibit metabolic reprogramming (*Warburg effect*) and secondary resistance to Imatinib via alternate pathways.
      - Metformin activates AMPK, inhibits mTORC1, and targets mitochondrial complex I, cutting off metabolic energy reserves and synergizing with Imatinib's competitive inhibition of BCR-ABL kinase.
    """)

render_back_to_top()
