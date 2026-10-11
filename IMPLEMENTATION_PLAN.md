# PharmaPath: Network Pharmacology & Graph Neural Network Pipeline
## Implementation Plan & Architectural Roadmap

### System Architecture Overview
```
+-----------------------------------------------------------------------------------+
|                                PHARMAPATH PIPELINE                                |
+-----------------------------------------------------------------------------------+
|  DATA INGESTION & HARMONIZATION                                                   |
|  - STRING v12 Homo sapiens PPI (Score >= 700, ENSP -> Gene Symbol mapping)       |
|  - ChEMBL API & DGIdb + Seed Targets (Metformin: T2D, Imatinib: CML)              |
|  - LINCS L1000 Chem Perturbation via Enrichr/gseapy (Per-gene perturbation score) |
|  - Open Targets GraphQL API (T2D & CML disease gene modules)                      |
|  - Reactome & KEGG Pathway Gene Sets                                              |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  M1: GRAPH SCAFFOLD & M2: SUBNETWORK EXTRACTION                                   |
|  - Weighted Undirected NetworkX Graph (Largest Connected Component)               |
|  - 2-Hop Neighborhood Subnetwork vs Random Walk with Restart (RWR, r=0.5)         |
|  - Export to GraphML & Parquet Edge Lists                                         |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  M3: EXPRESSION OVERLAY & PATHWAY ENRICHMENT                                      |
|  - LINCS z-score / log2FC node feature overlay                                    |
|  - ORA Enrichment (Reactome & KEGG) on perturbed nodes and subnetwork             |
|  - Biological sanity checks (AMPK/mTOR for Metformin; BCR-ABL/TK for Imatinib)    |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  M4: NETWORK TOPOLOGY & DISEASE PROXIMITY                                         |
|  - Centralities (Degree, Betweenness, Closeness, Eigenvector) -> Hubs/Bottlenecks  |
|  - Louvain Community Detection (Modularity, community functional profiling)       |
|  - Guney et al. (2016) Closest-Distance Disease Proximity (z-score vs 1000 nulls)  |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  M5: GRAPH NEURAL NETWORK LINK PREDICTION                                         |
|  - PPI Link Prediction: Node2Vec+LogReg, GraphSAGE, Graph Autoencoder (GAE)       |
|  - AUROC & Average Precision on leak-free RandomLinkSplit test edges              |
|  - Drug-Target Link Prediction: Leave-targets-out validation (Hits@K, MRR)         |
|  - Top 20 Repurposing / Off-target hypotheses per drug with confidence scores     |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  M6: TWO-DRUG COMPARISON & M7: VALIDATION                                         |
|  - Jaccard similarity (targets, subnetworks, pathways, modules)                   |
|  - Shortest-path topological separation (s_AB) and combination therapy insights   |
|  - Automated validation audit & PubMed literature search links for top 5 links    |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|  INTERACTIVE APPLICATION & REPORTING                                              |
|  - Streamlit Multi-Page App (PyVis network visualization, filtering, explorer)    |
|  - CLI Orchestrator: python scripts/run_all.py                                    |
|  - PyTest Test Suite                                                              |
|  - Publication-Quality Final Report (reports/final_report.md) & Defense Slides    |
+-----------------------------------------------------------------------------------+
```

### Execution Phases:
1. **Phase 0**: Directory layout, `requirements.txt`, `config/drugs.yaml`, `config/params.yaml`.
2. **Phase 1**: Real-World Data Retrieval (STRING v12, ChEMBL REST, LINCS L1000 Enrichr, Open Targets GraphQL) & PPI Construction (M1).
3. **Phase 2**: Subnetwork Extraction (2-hop vs RWR) (M2).
4. **Phase 3**: Expression Overlay & Pathway Enrichment (M3).
5. **Phase 4**: Network Analytics: Centralities, Louvain Communities & Guney Disease Proximity (M4).
6. **Phase 5**: GNN Link Prediction (Node2Vec, GraphSAGE, GAE) & Drug-Target Recovery (M5).
7. **Phase 6**: Two-Drug Comparison (M6).
8. **Phase 7**: Automated Validation & Literature Cross-Check (M7).
9. **Phase 8**: Master Script (`scripts/run_all.py`), Unit Tests (`pytest`), and Notebooks.
10. **Phase 9**: Interactive Streamlit Dashboard (`app/`).
11. **Phase 10**: Reports (`final_report.md`, `presentation_outline.md`, `README.md`).
