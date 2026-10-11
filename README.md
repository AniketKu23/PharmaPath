# PharmaPath: Multi-Omics Network-Pharmacology & GNN Discovery Platform

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![PyTorch 2.6](https://img.shields.io/badge/PyTorch-2.6-EE4C2C.svg)](https://pytorch.org/)
[![PyG](https://img.shields.io/badge/PyTorch_Geometric-Inductive_GNN-3C2179.svg)](https://pyg.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black.svg)](https://vercel.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 100% Passed](https://img.shields.io/badge/pytest-passed-brightgreen.svg)](tests/)

PharmaPath is an end-to-end, multi-omics network-pharmacology pipeline and Graph Neural Network (GNN) discovery platform. It models how diverse pharmacological agents perturb the human Protein-Protein Interaction (PPI) interactome scaffold to address four fundamental questions:
1. **Subnetwork & Pathway Perturbation**: Which interactome modules and signaling pathways does a drug perturb?
2. **Disease Module Localization**: Is the drug topologically proximate to its corresponding disease module?
3. **Topological Role Identification**: Which hub and bottleneck proteins mediate efficacy, resistance, or toxicity?
4. **Leak-Free Link Prediction**: Can inductive Graph Neural Networks predict novel drug-protein targets and off-target repurposing leads without data leakage?

The platform investigates two canonical pharmacological archetypes:
- **Metformin**: An indirect, multi-target metabolic regulator prescribed for **Type 2 Diabetes (T2D)** (targeting Mitochondrial Complex I and AMPK subunits; 61 targets in PPI LCC).
- **Imatinib (Gleevec)**: A precision oncogenic tyrosine kinase inhibitor prescribed for **Chronic Myeloid Leukemia (CML)** (targeting BCR-ABL1, KIT, PDGFRA, PDGFRB; 10 targets in PPI LCC).

---

## Deploy to Vercel from GitHub

This repository is pre-configured with `vercel.json` and `.vercelignore` for zero-configuration deployment to Vercel.

### Step 1: Initialize Git and Push to GitHub

In your project directory, run:

```bash
# Initialize git repository
git init

# Add all files (large raw PPI data is automatically excluded via .gitignore)
git add .

# Create initial commit
git commit -m "feat: initial commit for PharmaPath discovery platform"

# Rename branch to main
git branch -M main

# Link to your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/<your-username>/PharmaPath.git

# Push to GitHub
git push -u origin main
```

### Step 2: Import Repository on Vercel

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** $\to$ **Project**.
3. Select your GitHub account and click **Import** next to `PharmaPath`.
4. In the **Configure Project** window:
   - **Framework Preset**: Select `Other` (or leave default).
   - **Root Directory**: Leave as `./` (the included `vercel.json` automatically routes traffic to `/website/`). Alternatively, you may select `website` as the root directory.
   - **Build and Output Settings**: Leave empty (no build step is required for static assets).
5. Click **Deploy**.

Your interactive discovery platform will be live within seconds at `https://<your-project>.vercel.app`.

### Alternative: Direct CLI Deployment via Vercel CLI

You can also deploy directly from your local terminal using `npx vercel`:

```bash
# Deploy to preview
npx vercel

# Deploy directly to production
npx vercel --prod
```

---

## Pipeline Architecture

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      1. Multi-Omics Data Ingestion                     │
 │   STRING v12 PPI (Score>=700) • ChEMBL / Seed Targets • LINCS L1000   │
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
 └────────────────────────────────────────────────────────────────────────┘
```

---

## Summary of Experimental Results

### 1. PPI Interactome Scaffold (STRING v12, Homo sapiens)
- **High-confidence physical interactome**: `combined_score >= 700`
- **Protein-to-gene mapping loss rate**: **0.0000%** (19,699 / 19,699 mapped)
- **Largest Connected Component (LCC)**: **15,882 nodes (98.03% of proteome)** and **236,712 unique undirected edges** (density = $0.001877$).

### 2. Subnetwork Extraction & Graph Density
- **Metformin**: RWR subnetwork density = **0.4377** (4,891 edges across 150 nodes; $2.5\times$ enrichment over 2-hop).
- **Imatinib**: RWR subnetwork density = **0.2464** (2,754 edges across 150 nodes; $1.4\times$ enrichment over 2-hop).

### 3. Pathway Over-Representation Analysis (KEGG 2021 & Reactome 2022)
- **Metformin Sanity Audit**: **PASSED** ($FDR < 0.05$ across *AMPK signaling*, *mTOR signaling*, *Insulin signaling*, *FoxO signaling*, and *Oxidative Phosphorylation* $p_{adj} = 1.26 \times 10^{-153}$).
- **Imatinib Sanity Audit**: **PASSED** ($FDR < 0.05$ across *Receptor Tyrosine Kinases*, *SCF-KIT*, *PDGFRA*, *PI3K-Akt*, and *Chronic Myeloid Leukemia* $p_{adj} = 1.25 \times 10^{-24}$).

### 4. Disease Proximity (Guney et al., 2016 Nature Communications)
*Tested against 1,000 degree-matched random node set permutations:*
- **Metformin -> Type 2 Diabetes**: Observed $d_c = 0.213$, Null Mean = $1.012 \pm 0.044$, **$z = -18.28$**, **$p = 0.0010$** (Highly Significant Proximity).
- **Imatinib -> Chronic Myeloid Leukemia**: Observed $d_c = 0.400$, Null Mean = $1.228 \pm 0.114$, **$z = -7.25$**, **$p = 0.0010$** (Highly Significant Proximity).
- **Negative Controls**: Metformin $\to$ CML ($z = +18.32, p = 1.0000$); Imatinib $\to$ T2D ($z = +1.18, p = 0.9650$).

### 5. Inductive GNN Link Prediction Benchmark (Zero Data Leakage)
*Evaluated on 23,671 held-out test edges:*
- **Node2Vec + Logistic Regression Baseline**: Test AUROC = 0.5000, Test AP = 0.5000.
- **GraphSAGE (2-layer inductive message passing)**: **Test AUROC = 0.8865**, **Test AP = 0.9008**.
- **Graph Autoencoder (GAE)**: **Test AUROC = 0.8832**, **Test AP = 0.8958**.
- **Leave-Targets-Out Target Recovery**:
  - Metformin: Hidden target `NDUFS7` ranked **#15 out of 15,882 proteome candidates** (**Hits@20 = 50.0%**, MRR = $0.0334$).
  - Imatinib: Hidden target `CSF1R` ranked **#85 out of 15,882 candidates** (Hits@100 = 50.0%).

### 6. Two-Drug Interactome Separation (Menche et al., 2015 Science)
- Direct target overlap: $0$ shared targets (Jaccard = $0.0000$).
- Target Separation: $s_{AB}^{\text{closest}} = \mathbf{+1.3503}$ ($s_{AB} > 0$ indicates distinct direct target modules).
- **Cross-Talk Infrastructure**: 347 shared nodes within 2-hop interactome scaffold (Jaccard = 0.5314), including **22 shared hubs** (AKT1, TP53, MAPK1, STAT3, SRC).
- **Combination Pharmacology**: Metformin selectively forces quiescent leukemic stem cells (LSCs) in CML out of dormancy via Complex I inhibition and AMPK activation, overcoming Imatinib monotherapy resistance.

---

## Local Installation & Execution

### 1. Prerequisites
- Python 3.10 or 3.11
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/<your-username>/PharmaPath.git
cd PharmaPath

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Web Application Locally
Launch the local web server:
```bash
python website/server.py
```
Open `http://localhost:8080` in your browser.

### 4. Run the Full End-to-End Computational Pipeline
Execute the master runner to reproduce every analytical module sequentially:
```bash
python scripts/run_all.py
```

### 5. Run Individual Pipeline Scripts
```bash
python scripts/01_build_graph.py          # Phase 1: Ingestion & PPI LCC Scaffold (M1)
python scripts/02_extract_subnetworks.py   # Phase 2: RWR & 2-Hop Subnetworks (M2)
python scripts/03_enrichment.py           # Phase 3: Expression & Pathway ORA (M3)
python scripts/04_network_analysis.py     # Phase 4: Centralities & Proximity (M4)
python scripts/05_gnn_models.py           # Phase 5: GNN Link Prediction (M5)
python scripts/06_comparison.py           # Phase 6: Two-Drug Comparison (M6)
python scripts/07_validation.py           # Phase 7: Automated Validation Audit (M7)
```

### 6. Run Unit Test Suite
```bash
pytest tests/ -v
```

### 7. Run Browser Verification Test Suite (Playwright)
```bash
python scripts/test_website_playwright.py
```

---

## Repository Structure

```
PharmaPath/
├── README.md                           # Project documentation, results, and deployment guide
├── requirements.txt                    # Pinned Python package dependencies
├── vercel.json                         # Vercel deployment routing configuration
├── .vercelignore                       # Vercel upload exclusions
├── .gitignore                          # Git tracking exclusions
├── pytest.ini                          # PyTest testpaths and configuration
├── config/
│   ├── drugs.yaml                      # Config-driven drug & target specifications
│   └── params.yaml                     # Algorithmic hyperparameters & seeds
├── data/
│   ├── PROVENANCE.md                   # Full audit trail of data downloads & versions
│   └── processed/                      # Cached graphml, parquet, and target files
├── src/pharmapath/                     # Core computational modules
│   ├── __init__.py
│   ├── config.py                       # Configuration loaders & paths
│   ├── data.py                         # Data ingestion (STRING, ChEMBL, LINCS, OpenTargets)
│   ├── graph.py                        # PPI scaffold, ENSP mapping, LCC extraction
│   ├── subnetwork.py                   # 2-Hop & RWR subnetwork algorithms
│   ├── enrichment.py                   # KEGG & Reactome ORA & sanity check
│   ├── centrality.py                   # Centralities, hubs & bottlenecks
│   ├── communities.py                  # Louvain modularity clustering
│   ├── proximity.py                    # Guney proximity & 1000x degree-matched null model
│   ├── models.py                       # Inductive GraphSAGE, GAE & leave-targets-out
│   ├── comparison.py                   # Menche separation s_AB & Jaccard overlaps
│   ├── validation.py                   # Automated QA audits & literature verification
│   └── viz.py                          # Network visualization generation
├── website/                            # Interactive web discovery platform
│   ├── index.html                      # Single-page application entry point
│   ├── vercel.json                     # Vercel configuration for website root
│   ├── css/
│   │   └── style.css                   # Obsidian carbon & vibrant orange theme styles
│   ├── js/
│   │   └── app.js                      # Interactivity, Chart.js & Vis.js integration
│   ├── data/                           # Serialized multi-omics graph & metrics JSONs
│   ├── figures/                        # High-resolution benchmark figures
│   └── vendor/                         # Localized Vis.js and Chart.js bundles
├── scripts/
│   ├── run_all.py                      # Master end-to-end pipeline orchestrator
│   ├── 01_build_graph.py
│   ├── 02_extract_subnetworks.py
│   ├── 03_enrichment.py
│   ├── 04_network_analysis.py
│   ├── 05_gnn_models.py
│   ├── 06_comparison.py
│   ├── 07_validation.py
│   └── test_website_playwright.py      # Automated browser inspection suite
├── tests/
│   ├── test_graph.py                   # Graph construction & LCC tests
│   ├── test_mapping.py                 # ENSP gene symbol mapping tests
│   ├── test_proximity.py               # Guney proximity & separation tests
│   └── test_leakage.py                 # Verifies zero data leakage in GNN splits
├── docs/                               # Detailed technical documentation
│   ├── WEBSITE_ARCHITECTURE_AND_HOW_IT_WORKS.md
│   └── DATA_INTERPRETATION_REAL_WORLD_IMPACT_AND_VIVA_QA.md
└── reports/
    ├── final_report.md                 # Full academic project report
    ├── presentation_outline.md         # Slide defense outline
    └── validation_audit.md             # Pillar verification audit report
```

---

## Methodological Limitations

1. **Computational Predictions vs. Direct Biochemical Proof**: GNN link predictions identify topological and functional proximity in the human interactome. They represent **computational hypotheses** for drug repurposing or off-target interaction, **not** experimental proof of direct biochemical binding.
2. **Interactome Ascertainment Bias**: The STRING interactome scaffold is inherently biased toward extensively studied oncology and disease genes (e.g., TP53, AKT1, SRC). While degree-matched null permutation models eliminated hub bias in proximity evaluations, graph embeddings remain influenced by degree density.
3. **LINCS L1000 Cell-Line Context**: LINCS chemical perturbation profiles reflect immortalized cell lines under specific dosages and timepoints, which may differ from in vivo tissue responses.

---

## Citations & References

- Guney, E., et al. (2016). *Network-based in silico drug efficacy screening.* Nature Communications, 7, 10331.
- Menche, J., et al. (2015). *Uncovering disease-disease relationships through the incomplete interactome.* Science, 347(6224), 1257601.
- Szklarczyk, D., et al. (2023). *The STRING database in 2023.* Nucleic Acids Research, 51(D1), D638-D646.
- Hamilton, W. L., et al. (2017). *Inductive representation learning on large graphs.* NeurIPS 2017.
- Kipf, T. N., & Welling, M. (2016). *Variational graph auto-encoders.* arXiv:1611.07308.
- Subramanian, A., et al. (2017). *A next generation connectivity map: L1000 platform.* Cell, 171(6), 1437-1452.
- Ochoa, D., et al. (2023). *Open Targets Platform.* Nucleic Acids Research, 51(D1), D1281-D1289.

---

## License

This project is licensed under the MIT License.
