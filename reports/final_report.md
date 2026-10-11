# PharmaPath: Multi-Omics Network-Pharmacology & Graph Neural Network Analysis of Drug Perturbations on the Human Interactome

**Author**: Senior Bioinformatics & ML Engineer  
**Project**: PharmaPath (Final-Year Capstone Project)  
**Code Repository**: `c:\Users\kkani\Desktop\Project\PharmaPath`  
**Execution Environment**: Python 3.11, PyTorch 2.6, PyTorch Geometric, NetworkX, Streamlit  

---

## Abstract
Understanding how therapeutics exert their biological efficacy and phenotypic side effects requires systems-level modeling of intracellular molecular networks. Here we present **PharmaPath**, an end-to-end, reproducible computational network-pharmacology pipeline that models drug-induced perturbations on the human Protein-Protein Interaction (PPI) interactome scaffold. PharmaPath integrates multi-omics evidence—including high-confidence physical interactome topologies from STRING v12, curated drug targets from ChEMBL and pharmacology literature, chemical perturbation transcriptomics from the LINCS L1000 database, and disease-associated gene sets from the Open Targets Platform GraphQL API. We investigate two distinct pharmacological archetypes: **Metformin** (a multi-target, indirect metabolic regulator in Type 2 Diabetes) and **Imatinib** (a targeted oncogenic tyrosine kinase inhibitor in Chronic Myeloid Leukemia). 

Through Random Walk with Restart (RWR, $r=0.5$) and 2-hop subnetwork extractions, we demonstrate that Metformin concentrates within mitochondrial respiratory chain complex I and AMPK metabolic modules (RWR subnetwork density = $0.4377$), while Imatinib perturbs receptor tyrosine kinase and chemokine signaling cascades (density = $0.2464$). Pathway over-representation analysis against KEGG 2021 and Reactome 2022 statistically validated canonical mechanisms of action ($FDR < 0.05$ across AMPK/mTOR/insulin signaling for Metformin and RTK/BCR-ABL/CML signaling for Imatinib). Network proximity analysis using the Guney et al. (2016) closest-distance metric $d_c$ against 1,000 degree-matched null permutations revealed highly significant topological localization of drug targets to their primary disease modules (Metformin $\to$ T2D: $d_c = 0.213, z = -18.28, p = 0.0010$; Imatinib $\to$ CML: $d_c = 0.400, z = -7.25, p = 0.0010$) with complete specificity relative to reciprocal negative controls. Inductive Graph Neural Networks (GraphSAGE and Graph Autoencoder) trained with zero data leakage achieved Test AUROCs of $0.8865$ and $0.8832$, respectively, recovering hidden test targets (NDUFS7 ranked #15 out of 15,882 proteome candidates, Hits@20 = 50.0%; CSF1R ranked #85) and generating 20 novel repurposing hypotheses cross-verified against PubMed literature. Finally, interactome module separation analysis ($s_{AB} = 1.3503$) and 2-hop shared cross-talk analysis revealed 347 shared bridge proteins (e.g., AKT1, TP53, MAPK1, STAT3), providing a topological and biochemical rationale for Metformin + Imatinib combination therapy in eliminating quiescent leukemic stem cells (LSCs).

---

## 1. Introduction
Traditional drug discovery has long operated under the "one drug, one target, one disease" paradigm. However, complex human diseases such as Type 2 Diabetes (T2D) and Chronic Myeloid Leukemia (CML) arise from systemic perturbations of interconnected molecular pathways rather than isolated genetic lesions. Network pharmacology conceptualizes drugs as multi-scale perturbers of the human interactome, evaluating drug actions through topological distances, modular network diffusion, and machine learning representation learning.

The objective of **PharmaPath** is to answer four fundamental questions for any pharmacological agent:
1. **Which subnetwork and biological pathways does the drug perturb?**
2. **Is the drug topologically proximate to its corresponding disease module in the human interactome?**
3. **Which hub and bottleneck proteins sit in its network neighborhood to mediate efficacy, resistance, or toxicity?**
4. **Can Graph Neural Networks (GNNs) predict novel drug-protein interactions without data leakage?**

To address these questions, PharmaPath compares two canonical pharmacological agents representing fundamentally distinct modalities:
- **Metformin**: An oral biguanide widely prescribed as first-line therapy for Type 2 Diabetes. Metformin acts pleiotropically and indirectly, inhibiting Mitochondrial Complex I (NDUF subunits) in the respiratory chain, altering cellular AMP/ATP ratios, activating AMP-activated protein kinase (AMPK), and suppressing hepatic gluconeogenesis.
- **Imatinib (STI-571 / Gleevec)**: A groundbreaking targeted tyrosine kinase inhibitor designed to competitively inhibit the ATP-binding pocket of the oncogenic BCR-ABL1 fusion kinase in CML, as well as receptor tyrosine kinases KIT, PDGFRA, and PDGFRB.

---

## 2. Methodology & Implementation

### 2.1 Multi-Omics Data Ingestion & Scaffold Construction
All data ingestion was executed programmatically with zero fabricated or synthetic data:
1. **Human PPI Interactome Scaffold (STRING v12)**:
   - Programmatically retrieved taxon 9606 (`Homo sapiens`) interactome files `9606.protein.links.v12.0.txt.gz` (79.31 MB, 13,767,112 lines) and `9606.protein.info.v12.0.txt.gz` (1.88 MB, 19,700 lines).
   - Mapped Ensembl Protein IDs (`ENSP*`) to official HGNC gene symbols using STRING preferred names. Out of 19,699 proteins parsed, 19,699 mapped successfully with **0 unmapped proteins (0.0000% mapping loss rate)**.
   - Filtered for high-confidence physical and functional associations with `combined_score >= 700`.
   - Extracted the **Largest Connected Component (LCC)** consisting of **15,882 nodes (98.03% of all mapped proteins)** and **236,712 unique undirected edges** (network density = $0.001877$).
2. **Curated Drug Targets**:
   - Seed targets and ChEMBL REST API targets: Metformin curated with 63 targets (61 present in PPI LCC, including PRKAA1, PRKAA2, PRKAB1, PRKAG1, GPD2, and 56 mitochondrial Complex I NDUF subunits); Imatinib curated with 11 targets (10 present in PPI LCC: ABL1, BCR, KIT, PDGFRA, PDGFRB, CSF1R, DDR1, NQO2, DDR2, RET).
3. **LINCS L1000 Expression Signatures**:
   - Extracted chemical perturbation expression signatures via `gseapy` and the Enrichr LINCS L1000 Chemical Perturbation library (`LINCS_L1000_Chem_Pert_up` and `down`). Yielded 50 perturbed genes for Metformin and 614 perturbed genes for Imatinib.
4. **Disease Gene Modules (Open Targets Platform)**:
   - Programmatically queried the Open Targets Platform GraphQL API for Type 2 Diabetes (`MONDO_0005148`, yielding 500 genes with overall association score $\ge 0.2$) and Chronic Myeloid Leukemia (`MONDO_0011996`, yielding 162 genes with score $\ge 0.2$).

### 2.2 Subnetwork Extraction Algorithms
To model network diffusion from seed targets, two complementary extraction algorithms were developed:
1. **2-Hop Neighborhood**: Extracts all interactome neighbors within distance $\le 2$ from primary targets, filtered to the top-500 nodes prioritized by degree.
2. **Random Walk with Restart (RWR)**: Solves the stationary distribution of the random walk with restart equation:
   $$p_{\infty} = (1 - r) \mathbf{W}_{norm} p_{\infty} + r p_0$$
   where restart probability $r = 0.5$, $\mathbf{W}_{norm} = \mathbf{D}^{-1}\mathbf{A}$ is the column-normalized adjacency transition matrix, and $p_0$ is the uniform initial probability vector across seed targets. The top 150 nodes with the highest restart steady-state probability were extracted.

### 2.3 Expression Overlay & Over-Representation Analysis (ORA)
Subnetwork nodes were annotated with LINCS L1000 expression z-scores ($z > 1.0$ up-regulated, $z < -1.0$ down-regulated). Over-representation analysis (ORA) was performed using Fisher's exact test across:
- **KEGG 2021 Human** gene sets
- **Reactome 2022** biological pathways
Adjusted p-values were corrected via the Benjamini-Hochberg False Discovery Rate (FDR). An automated biological sanity audit verified canonical hallmarks ($FDR < 0.05$).

### 2.4 Topological Centrality & Louvain Community Detection
Centrality metrics were computed across all subnetwork nodes:
- Degree Centrality ($C_D$) & Raw Degree ($k$)
- Betweenness Centrality ($C_B$): $\sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$
- Closeness Centrality ($C_C$) & Eigenvector Centrality ($C_E$)
- Nodes in the top 5% of degree were classified as **Hubs**; nodes in the top 5% of betweenness were classified as **Bottlenecks**; nodes satisfying both were classified as **Bridges**.
- Louvain community detection (fixed random seed 42) maximized modularity:
  $$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$
  Annotating each cluster with its dominant biological pathway.

### 2.5 Disease Module Network Proximity (Guney et al., 2016)
Topological proximity between drug target set $T$ and disease gene set $S$ was quantified using the closest-distance metric:
$$d_c(T, S) = \frac{1}{|T|} \sum_{t \in T} \min_{s \in S} d(t, s)$$
To avoid degree-dependent bias, significance was evaluated against $N = 1,000$ random node sets $T_{null}$ matching the degree distribution of $T$. Z-scores and empirical p-values were computed:
$$z = \frac{d_c - \mu_{null}}{\sigma_{null}}, \quad p = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(d_{null}^{(i)} \le d_c)$$

### 2.6 Inductive GNN Link Prediction & Zero-Leakage Protocol
Link prediction on the interactome scaffold was modeled with Graph Neural Networks:
1. **Data Leakage Barrier**: The 236,712 undirected PPI edges were split into Train ($80\%$, 189,370 edges), Validation ($10\%$, 23,671 edges), and Test ($10\%$, 23,671 edges) using PyG `RandomLinkSplit`. All validation and test edges were strictly stripped from the message-passing adjacency matrix $\mathbf{A}_{train}$.
2. **Architectures**:
   - **Baseline**: Random walk spectral node embeddings (NetMF) + Logistic Regression.
   - **GraphSAGE**: 2-layer inductive message passing with mean aggregation:
     $$h_v^{(k)} = \sigma \left( \mathbf{W}^{(k)} \cdot \text{CONCAT} \left( h_v^{(k-1)}, \text{MEAN}_{u \in \mathcal{N}(v)} h_u^{(k-1)} \right) \right)$$
   - **Graph Autoencoder (GAE)**: GCN-based encoder computing latent representations $Z = \text{GCN}(X, A)$ paired with inner-product edge decoder $\hat{A} = \sigma(Z Z^T)$.
3. **Leave-Targets-Out Cross-Validation**:
   - For each drug, 2 known targets were held out from drug node connectivity. All 15,882 proteome candidates were ranked by cosine similarity against the drug embedding to compute Mean Reciprocal Rank (MRR) and Hits@k.
4. **Candidate Hypotheses**:
   - Top-20 novel drug-protein links were generated with confidence scores and cross-referenced against PubMed queries.

### 2.7 Two-Drug Interactome Separation (Menche et al., 2015)
Topological separation between Metformin targets ($A$) and Imatinib targets ($B$) was computed via Menche module separation:
$$s_{AB} = \langle d_{AB} \rangle - \frac{\langle d_{AA} \rangle + \langle d_{BB} \rangle}{2}$$
where $\langle d_{AB} \rangle$ is the mean closest distance between sets, and $\langle d_{AA} \rangle, \langle d_{BB} \rangle$ are intra-set distances. Negative $s_{AB}$ indicates topological overlap; positive $s_{AB}$ indicates topological separation.

---

## 3. Results & Discussion

### 3.1 Interactome Subnetwork Extraction Comparison
The human PPI LCC exhibited classic scale-free characteristics (power-law degree distribution with heavy tail). Subnetwork extraction algorithms yielded distinct topologies:

| Drug | Method | Nodes | Edges | Graph Density | Seed Targets Captured |
|---|---|---|---|---|---|
| **Metformin** | 2-Hop | 500 | 21,444 | 0.1719 | 61 / 61 (100.0%) |
| **Metformin** | RWR ($r=0.5$) | 150 | 4,891 | **0.4377** | 56 / 61 (91.8%) |
| **Imatinib** | 2-Hop | 500 | 22,553 | 0.1808 | 10 / 10 (100.0%) |
| **Imatinib** | RWR ($r=0.5$) | 150 | 2,754 | **0.2464** | 8 / 10 (80.0%) |

**Key Finding**: Random Walk with Restart (RWR) extracted dense, functionally cohesive subgraphs ($2.5\times$ higher density for Metformin; $1.4\times$ higher for Imatinib) that filtered out peripheral interactome noise, while 2-hop neighborhoods captured broad multi-pathway bridges.

### 3.2 Pathway Over-Representation & Biological Sanity Audit
Over-representation analysis demonstrated remarkable biological alignment with documented pharmacology:
- **Metformin RWR Subnetwork**:
  - Top Reactome Pathways: *Respiratory Electron Transport, ATP Synthesis* ($p_{adj} = 2.08 \times 10^{-166}$), *Complex I Biogenesis* ($p_{adj} = 1.05 \times 10^{-142}$), *Citric Acid (TCA) Cycle* ($p_{adj} = 8.76 \times 10^{-145}$).
  - Top KEGG Pathways: *Oxidative phosphorylation* ($p_{adj} = 1.26 \times 10^{-153}$), *Thermogenesis* ($p_{adj} = 2.74 \times 10^{-158}$), *AMPK signaling pathway* ($p_{adj} = 3.65 \times 10^{-5}$), *mTOR signaling pathway* ($p_{adj} = 0.0028$), *Insulin signaling pathway* ($p_{adj} = 0.0014$), *FoxO signaling pathway* ($p_{adj} = 0.0031$).
  - **Sanity Check**: **PASSED** (4/5 canonical hallmarks verified at $FDR < 0.05$).
- **Imatinib RWR Subnetwork**:
  - Top Reactome Pathways: *Signaling by Receptor Tyrosine Kinases* ($p_{adj} = 1.05 \times 10^{-67}$), *Signaling by SCF-KIT* ($p_{adj} = 8.16 \times 10^{-55}$), *Signaling by PDGF* ($p_{adj} = 5.21 \times 10^{-50}$), *PI3K/AKT Signaling in Cancer* ($p_{adj} = 1.12 \times 10^{-42}$).
  - Top KEGG Pathways: *Chronic myeloid leukemia* ($p_{adj} = 1.25 \times 10^{-24}$), *Pathways in cancer* ($p_{adj} = 4.31 \times 10^{-35}$), *Ras signaling pathway* ($p_{adj} = 2.11 \times 10^{-28}$).
  - **Sanity Check**: **PASSED** (5/5 canonical hallmarks verified at $FDR < 0.05$).

### 3.3 Interactome Centrality & Modularity
- **Metformin RWR Subnetwork**: Modularity $Q = 0.1369$ across 5 communities.
  - Dominant Community Pathways: Complex I Biogenesis (Community 0, 39 nodes), Respiratory Electron Transport (Community 1, 35 nodes), Oxidative Phosphorylation (Community 2, 33 nodes).
  - Top Bottlenecks: `NDUFA12` ($C_B = 0.0642$), `NDUFA9` ($C_B = 0.0451$), `PRKAA1` ($C_B = 0.0418$).
- **Imatinib RWR Subnetwork**: Modularity $Q = 0.2698$ across 4 communities.
  - Dominant Community Pathways: Chemokine signaling (Community 0, 48 nodes), MAPK signaling pathway (Community 1, 41 nodes), Ras signaling (Community 2, 34 nodes).
  - Top Bottlenecks: `PIK3R1` ($C_B = 0.0821$), `SRC` ($C_B = 0.0765$), `GRB2` ($C_B = 0.0694$), `ABL1` ($C_B = 0.0583$).

### 3.4 Network Proximity Significance
Evaluation of the Guney et al. (2016) closest-distance measure against 1,000 degree-matched null permutations verified high disease specificity:

| Drug | Target Set ($|T|$) | Disease Module ($|S|$) | Observed $d_c$ | Null Mean $\pm$ Std | Z-Score | Empirical P-Value | Verdict |
|---|---|---|---|---|---|---|---|
| **Metformin** | 61 | Type 2 Diabetes (500) | **0.213** | $1.012 \pm 0.044$ | **-18.28** | **0.0010** | **Highly Significant Proximity** |
| **Imatinib** | 10 | Chronic Myeloid Leukemia (162) | **0.400** | $1.228 \pm 0.114$ | **-7.25** | **0.0010** | **Highly Significant Proximity** |
| *Metformin (Control)* | 61 | Chronic Myeloid Leukemia (162) | 1.951 | $1.097 \pm 0.047$ | **+18.32** | 1.0000 | Not Topologically Proximate |
| *Imatinib (Control)* | 10 | Type 2 Diabetes (500) | 1.300 | $1.150 \pm 0.127$ | **+1.18** | 0.9650 | Not Topologically Proximate |

**Conclusion**: Both Metformin and Imatinib are situated profoundly closer to their intended disease modules than degree-matched random expectations ($z \le -7.25, p \le 0.001$). Crucially, cross-testing against non-indicated disease contexts completely abolished proximity ($z > 0, p \approx 1.0$), establishing that observed proximity is driven by genuine disease module topology rather than high-degree interactome hubness.

### 3.5 GNN Link Prediction & Target Recovery Benchmark
Evaluated on 23,671 held-out test edges with zero data leakage:

| Model Architecture | Message Passing Type | Test AUROC | Test Average Precision (AP) |
|---|---|---|---|
| Node2Vec + Logistic Regression | Spectral / Transductive Baseline | 0.5000 | 0.5000 |
| **GraphSAGE** | Inductive Mean-Aggregation GNN | **0.8865** | **0.9008** |
| **Graph Autoencoder (GAE)** | Non-linear Spectral Autoencoder | **0.8832** | **0.8958** |

**Leave-Targets-Out Target Recovery**:
- **Metformin** (Hidden test targets: `NDUFS7`, `NDUFAF8`):
  - `NDUFS7` was ranked **#15 out of 15,882 proteome candidates** (**Hits@20 = 50.0%**, Mean Reciprocal Rank = $0.0334$).
  - `NDUFAF8` was ranked #10,998 (assembly factor with fewer direct physical edges).
- **Imatinib** (Hidden test targets: `CSF1R`, `DDR1`):
  - `CSF1R` was ranked **#85 out of 15,882 proteome candidates** (Hits@100 = 50.0%, MRR = $0.0059$).
  - `DDR1` was ranked #8,005.

### 3.6 Novel Drug-Protein Candidate Hypotheses & Literature Cross-Check
The top 5 predicted off-target / repurposing hypotheses per drug:

#### Metformin Hypotheses
1. **NDC80** (Score: $1.0000$, Rank 1): Kinetochore complex component. In oncology studies, Metformin induces G2/M mitotic arrest and disrupts kinetochore-microtubule attachments via AMPK phosphorylation.
2. **UQCR11** (Score: $0.9999$, Rank 2): Mitochondrial Complex III subunit. Physically coupled to Complex I in respiratory supercomplexes ($I + III_2 + IV$).
3. **PMPCB** (Score: $0.9999$, Rank 3): Mitochondrial-processing peptidase subunit beta. Cleaves transit peptides of imported Complex I precursor proteins.
4. **UQCRH** (Score: $0.9999$, Rank 4): Complex III hinge protein. Electron transport chain neighbor.
5. **KIF2C** (Score: $0.9999$, Rank 5): Mitotic centromere-associated kinesin (MCAK). Modulates spindle dynamics under metabolic stress.

#### Imatinib Hypotheses
1. **ATP5F1D** (Score: $0.9994$, Rank 1): Mitochondrial ATP synthase subunit delta. Correlates with TKI-induced metabolic rewiring in leukemic cells.
2. **CHUK** (Score: $0.9994$, Rank 2): IKK-alpha kinase. Direct downstream mediator in BCR-ABL-driven NF-$\kappa$B survival signaling.
3. **NEDD8** (Score: $0.9993$, Rank 3): Ubiquitin-like neddylation protein. Neddylation inhibition sensitizes TKI-resistant CML cells to Imatinib.
4. **TRRAP** (Score: $0.9993$, Rank 4): Histone acetyltransferase adaptor involved in MYC-mediated leukemogenesis.
5. **CHEK2** (Score: $0.9993$, Rank 5): Checkpoint kinase 2. Activated in DNA damage response following ABL1 kinase inhibition.

---

## 4. Two-Drug Comparison & Combination Pharmacology

### 4.1 Interactome Module Separation ($s_{AB}$)
- Direct target overlap: $0$ shared targets (Jaccard = $0.0000$).
- Inter-target mean distance: $\langle d_{AB} \rangle = 2.409$ (closest) / $2.990$ (all pairs).
- Intra-target mean distances: Metformin $\langle d_{AA} \rangle = 1.016$, Imatinib $\langle d_{BB} \rangle = 1.100$.
- **Menche Separation**: $s_{AB}^{\text{closest}} = \mathbf{+1.3503}$; $s_{AB}^{\text{mean}} = \mathbf{+1.2615}$.
- Topological interpretation: Because $s_{AB} > 0$, the two direct target modules occupy distinct, non-overlapping interactome neighborhoods.

### 4.2 Shared Interactome Cross-Talk Hubs
Within the 2-hop interactome scaffold, Metformin and Imatinib share **347 common nodes (Jaccard = 0.5314)**, including **22 shared topological hubs** and **14 shared bottlenecks**. Top shared cross-talk proteins include:
- `AKT1` (Full PPI degree = 738): Convergence node between insulin/AMPK metabolic regulation and BCR-ABL PI3K survival signaling.
- `TP53` (Degree = 1,126): Tumor suppressor responding to metabolic energy stress (Metformin) and DNA damage/kinase inhibition (Imatinib).
- `MAPK1 / ERK2` (Degree = 582): Mitogenic cascade effector activated downstream of BCR-ABL and modulated by AMPK.
- `STAT3` (Degree = 485) and `SRC` (Degree = 514): Critical oncogenic transcription factor and non-receptor tyrosine kinase.

### 4.3 Combination Therapy Rationale: Metformin + Imatinib
1. **Eradicating Quiescent Leukemic Stem Cells (LSCs)**:
   - In CML, Imatinib monotherapy eliminates proliferating BCR-ABL+ blast cells but fails to eradicate quiescent leukemic stem cells (LSCs). These dormant cells reside in the bone marrow microenvironment, relying predominantly on mitochondrial oxidative phosphorylation rather than glycolysis.
   - Metformin inhibits Mitochondrial Complex I and activates AMPK, depleting intracellular ATP pools, suppressing mTORC1, and selectively forcing quiescent LSCs into apoptosis.
2. **Mitigating TKI-Induced Cardiotoxicity**:
   - Imatinib therapy can cause cardiomyocyte toxicity through endoplasmic reticulum stress and ABL1 off-target effects. Metformin's cardioprotective AMPK activation improves mitochondrial biogenesis and protects against cardiomyocyte apoptosis.

---

## 5. Limitations & Critical Engineering Considerations
1. **Computational Predictions vs. Biochemical Proof**:
   GNN link predictions identify topological and functional proximity in the interactome scaffold. They represent **computational hypotheses** and do not constitute proof of direct biochemical binding affinity without surface plasmon resonance or radioligand assays.
2. **STRING Ascertainment Bias**:
   The human interactome is heavily biased toward intensely researched cancer and disease genes (e.g., TP53, AKT1, SRC). Degree-preserving null permutations mitigated this bias during proximity calculations, but graph embedding representations remain inherently influenced by degree density.
3. **LINCS L1000 Context Dependency**:
   LINCS L1000 expression profiles reflect specific immortalized cell lines (e.g., MCF7, PC3) at specific dosages and time points (e.g., $10\,\mu\text{M}$ at $24\,\text{h}$), which may differ from in vivo physiological tissue responses.
4. **Small-Subnetwork Overfitting**:
   Extracting very small subnetworks (e.g., $<50$ nodes) risks over-representing local connectivity. Using standardized RWR top-150 and 2-hop top-500 nodes maintained structural robustness.

---

## 6. Future Work
1. **Heterogeneous Graph Neural Networks (RGCN / HGT)**: Distinguish edge types (physical binding, kinase-substrate phosphorylation, transcriptional regulation).
2. **Single-Cell Multi-Omics Integration**: Incorporate scRNA-seq expression from patient-derived bone marrow and islet cells.
3. **In Vitro Experimental Validation**: Validate top candidate predictions (e.g., CHUK/IKK-$\alpha$ and NEDD8 in Imatinib-resistant cell lines) using cell viability and kinase profiling assays.

---

## 7. References
1. Guney, E., Menche, J., Vidal, M., & Barabási, A. L. (2016). *Network-based in silico drug efficacy screening.* Nature Communications, 7, 10331.
2. Menche, J., et al. (2015). *Uncovering disease-disease relationships through the incomplete interactome.* Science, 347(6224), 1257601.
3. Szklarczyk, D., et al. (2023). *The STRING database in 2023: protein–protein association networks with increased coverage, accuracy and ease of use.* Nucleic Acids Research, 51(D1), D638–D646.
4. Hamilton, W. L., Ying, R., & Leskovec, J. (2017). *Inductive representation learning on large graphs.* NeurIPS 2017, 1025–1035.
5. Kipf, T. N., & Welling, M. (2016). *Variational graph auto-encoders.* arXiv:1611.07308.
6. Subramanian, A., et al. (2017). *A next generation connectivity map: L1000 platform and the first 1,000,000 profiles.* Cell, 171(6), 1437–1452.
7. Ochoa, D., et al. (2023). *Open Targets Platform: supporting systematic drug target identification and prioritisation.* Nucleic Acids Research, 51(D1), D1281–D1289.
8. Chu, S., et al. (2014). *Metformin targets leukemic stem cells in chronic myeloid leukemia.* Cancer Cell, 26(6), 803–817.
