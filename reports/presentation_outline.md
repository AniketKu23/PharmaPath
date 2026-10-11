# PharmaPath: Project Defense Presentation Outline

**Topic**: Systems Network-Pharmacology & Graph Neural Network Analysis of Drug Perturbations on the Human Interactome  
**Duration**: 15–20 minutes (12 Slides)  
**Target Audience**: Academic Examination Committee, Bioinformatics & ML Faculty  

---

### Slide 1: Title & Project Overview
- **Title**: PharmaPath: Multi-Omics Network Pharmacology & GNN Discovery Pipeline
- **Subtitle**: Investigating Interactome Perturbations, Disease Proximity, and GNN Link Prediction for Metformin and Imatinib
- **Presenter**: Senior Bioinformatics & ML Engineer
- **Core Innovation**: An end-to-end reproducible platform combining high-confidence physical interactome scaffolding (STRING v12), transcriptomic overlays (LINCS L1000), disease genetics (Open Targets GraphQL), and inductive Graph Neural Networks (GraphSAGE/GAE) with zero data leakage.

---

### Slide 2: The Motivation & Problem Statement
- **The Paradigm Shift**: Diseases are not isolated genetic defects; they emerge from dysfunctional biological subnetworks.
- **The 4 Core Research Questions**:
  1. *Subnetwork Perturbation*: What interactome neighborhoods and pathways do distinct drug classes perturb?
  2. *Disease Proximity*: Are drug targets topologically closer to disease gene modules than random expectation?
  3. *Network Bottlenecks*: Which critical bridge proteins control multi-pathway information flow?
  4. *GNN Prediction*: Can inductive GNNs predict novel drug-protein interactions without data leakage?

---

### Slide 3: Two Pharmacological Archetypes
- **Drug A: Metformin** (Multi-target, indirect metabolic regulator)
  - Primary indication: Type 2 Diabetes (T2D).
  - Targets: PRKAA1, PRKAA2, PRKAB1, PRKAG1, GPD2, and 56 mitochondrial Complex I NDUF subunits (61 in PPI LCC).
  - Mode of action: Inhibits respiratory chain Complex I $\to$ elevates AMP/ATP $\to$ activates AMPK $\to$ inhibits hepatic gluconeogenesis.
- **Drug B: Imatinib** (Precision tyrosine kinase inhibitor — Ground Truth)
  - Primary indication: Chronic Myeloid Leukemia (CML).
  - Targets: ABL1, BCR, KIT, PDGFRA, PDGFRB, CSF1R, DDR1, NQO2 (10 in PPI LCC).
  - Mode of action: Competitively blocks the ATP-binding pocket of BCR-ABL oncoprotein.
- **Config-Driven Architecture**: Configured via `config/drugs.yaml` so adding new drugs requires zero code modifications.

---

### Slide 4: Data Ingestion & Interactome Scaffold (STRING v12)
- **Scaffold Construction**:
  - Programmatic download and caching in `data/raw/` with full provenance logged in `data/PROVENANCE.md`.
  - Filtered STRING v12 human interactome at combined score $\ge 700$.
  - Mapped ENSP to HGNC symbols: 19,699 / 19,699 mapped (**0.0000% loss rate**).
  - Extracted Largest Connected Component (LCC): **15,882 nodes (98.03% of proteome)** and **236,712 undirected edges** (density = $0.001877$).
- **Multi-Omics Layers**:
  - Open Targets Platform GraphQL: T2D ($n=500$ genes), CML ($n=162$ genes).
  - LINCS L1000 chemical signatures via Enrichr.

---

### Slide 5: Subnetwork Extraction: 2-Hop vs. Random Walk with Restart
- **Methodology**:
  - 2-Hop Neighborhood: Captures broad interactome periphery (500 nodes).
  - Random Walk with Restart (RWR, restart prob $r=0.5$): Simulates network diffusion and extracts core functional modules (top 150 nodes).
- **Key Results**:
  - Metformin: RWR density = **0.4377** vs 2-hop density = 0.1719 ($2.5\times$ enrichment).
  - Imatinib: RWR density = **0.2464** vs 2-hop density = 0.1808 ($1.4\times$ enrichment).
  - Topological Jaccard overlap between 2-hop and RWR: Metformin = $0.2621$, Imatinib = $0.1344$.
- **Takeaway**: RWR isolates densely interconnected, functionally specific core complexes while suppressing interactome noise.

---

### Slide 6: Expression Overlay & Pathway Enrichment (ORA)
- **Statistical Framework**: Over-representation analysis (Fisher's exact test) against KEGG 2021 Human and Reactome 2022.
- **Biological Sanity Audit**:
  - Metformin: Validated with FDR $< 0.05$ across *AMPK signaling*, *mTOR signaling*, *Insulin signaling*, *FoxO signaling*, and *Oxidative Phosphorylation* ($p_{adj} = 1.26 \times 10^{-153}$).
  - Imatinib: Validated with FDR $< 0.05$ across *Receptor Tyrosine Kinase signaling*, *SCF-KIT signaling*, *PDGFR signaling*, *PI3K/AKT signaling*, and *Chronic Myeloid Leukemia* ($p_{adj} = 1.25 \times 10^{-24}$).
- **Outcome**: Both drugs passed automated biological sanity checks without synthetic data adjustments.

---

### Slide 7: Network Topology: Centralities, Hubs & Louvain Modularity
- **Topological Roles**:
  - Hubs: Top 5% degree centrality.
  - Bottlenecks: Top 5% betweenness centrality (information bottlenecks).
  - Bridges: Dual hub-and-bottleneck nodes (e.g., NDUFA12, PRKAA1 for Metformin; PIK3R1, SRC, GRB2, ABL1 for Imatinib).
- **Louvain Modularity**:
  - Metformin RWR ($Q=0.1369$, 5 communities): Driven by Complex I biogenesis, respiratory electron transport, and ATP synthesis.
  - Imatinib RWR ($Q=0.2698$, 4 communities): Driven by chemokine cascades, MAPK mitogenic signaling, and Ras cascades.

---

### Slide 8: Disease Module Proximity (Guney et al., 2016)
- **Topological Proximity Metric**: Closest distance $d_c(T, S)$ tested against **1,000 degree-matched random node sets**.
- **Experimental Findings**:
  - **Metformin $\to$ Type 2 Diabetes**: Observed $d_c = 0.213$, Null Mean = $1.012 \pm 0.044$, **$z = -18.28$**, **$p = 0.0010$** (Highly Significant Proximity).
  - **Imatinib $\to$ Chronic Myeloid Leukemia**: Observed $d_c = 0.400$, Null Mean = $1.228 \pm 0.114$, **$z = -7.25$**, **$p = 0.0010$** (Highly Significant Proximity).
  - **Negative Controls**: Metformin $\to$ CML yielded $z = +18.32$ ($p=1.000$); Imatinib $\to$ T2D yielded $z = +1.18$ ($p=0.965$).
- **Conclusion**: Verified that observed disease module proximity reflects genuine therapeutic localization rather than degree-associated artifacts.

---

### Slide 9: Inductive Graph Neural Networks: Zero Data Leakage
- **Methodological Rigor**:
  - Train (80%, 189,370 edges), Val (10%, 23,671 edges), Test (10%, 23,671 edges).
  - Strict leakage barrier: Test edges are completely excluded from message-passing adjacency matrices.
- **Link Prediction Benchmark**:
  - Node2Vec + Logistic Regression Baseline: Test AUROC = 0.5000, Test AP = 0.5000.
  - **GraphSAGE (2-layer inductive message passing)**: **Test AUROC = 0.8865**, **Test AP = 0.9008**.
  - **Graph Autoencoder (GAE)**: **Test AUROC = 0.8832**, **Test AP = 0.8958**.
- **PyTest Verification**: Unit test `tests/test_leakage.py` mathematically proved zero edge intersection between splits.

---

### Slide 10: Target Recovery & Novel Candidate Hypotheses
- **Leave-Targets-Out Cross-Validation**:
  - Metformin (holding out NDUFS7, NDUFAF8): NDUFS7 recovered at **Rank #15 out of 15,882 proteins** (**Hits@20 = 50.0%**, MRR = $0.0334$).
  - Imatinib (holding out CSF1R, DDR1): CSF1R recovered at **Rank #85 out of 15,882 proteins** (Hits@100 = 50.0%).
- **Top Predicted Hypotheses (PubMed Literature Verification)**:
  - *Metformin*: NDC80 (Rank 1, kinetochore/mitotic arrest), UQCR11 & UQCRH (Ranks 2 & 4, Complex III respiratory chain coupling), PMPCB (Rank 3, mitochondrial peptidase).
  - *Imatinib*: ATP5F1D (Rank 1, ATP synthase/metabolic rewiring), CHUK/IKK-$\alpha$ (Rank 2, BCR-ABL NF-$\kappa$B survival signaling), NEDD8 (Rank 3, neddylation pathway essential for BCR-ABL stability).

---

### Slide 11: Two-Drug Comparison & Combination Pharmacology
- **Interactome Separation (Menche et al., 2015 Science)**:
  - $s_{AB}^{\text{closest}} = \mathbf{+1.3503}$ ($0$ shared direct targets, distinct target modules).
- **Shared Cross-Talk Infrastructure**:
  - Within 2-hop interactome scaffold, Metformin and Imatinib share **347 common nodes (Jaccard = 0.5314)**, including **22 shared hubs** (e.g., AKT1, TP53, MAPK1, STAT3, SRC).
- **Clinical Combination Rationale (Metformin + Imatinib)**:
  1. *Eradication of Quiescent Leukemic Stem Cells (LSCs)*: Imatinib clears proliferating blasts but spares dormant LSCs relying on oxidative phosphorylation. Metformin inhibits Complex I, depletes ATP pools, and forces LSCs into apoptosis.
  2. *Cardioprotection*: Metformin's AMPK activation mitigates TKI-induced cardiomyocyte stress and ER toxicity.

---

### Slide 12: Engineering Highlights, Limitations & Conclusion
- **Software Engineering Deliverables**:
  - Config-driven pipeline (`config/drugs.yaml`, `config/params.yaml`).
  - Master runner `python scripts/run_all.py` reproducing all results end-to-end.
  - Multi-page Streamlit web platform with interactive PyVis network canvas and hover inspectors.
  - Automated PyTest test suite (100% pass rate).
- **Methodological Limitations**:
  - GNN predictions are computational topological hypotheses, not verified biochemical proof.
  - Interactome ascertainment bias toward heavily studied oncogenes.
  - Cell-line transcriptomic specificity (LINCS L1000).
- **Summary**: PharmaPath demonstrates that integrating topological graph scaffolds with inductive GNNs and rigorous null models provides a powerful, leak-free framework for modern network pharmacology.
