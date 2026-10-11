# 🌐 PharmaPath: Comprehensive Website Architecture & Technical Guide

---

## 1. Executive Technical Overview

The **PharmaPath Interactive Discovery Platform** is an enterprise-grade, high-performance web interface engineered to explore multi-omics network-pharmacology and Graph Neural Network (GNN) discoveries. It is designed with a modern, cyber-biotechnology aesthetic featuring the **McLaren Orange (`#FF8000`)** dark design system, glassmorphic UI panels, interactive HTML5 canvas particle physics, WebGL/Vis.js graph physics engines, and dynamic Chart.js visualizations.

The web application runs with **zero external backend dependencies** during client sessions—it serves pre-computed, multi-omics graph analytics and machine learning benchmarks through a lightweight asynchronous JSON data pipeline served via Python's built-in HTTP server or any standard web server.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PharmaPath Web Architecture                     │
├────────────────────────────────────────────────────────────────────────┤
│  [Client Browser: http://localhost:8080]                                │
│   │                                                                    │
│   ├── index.html ───────── Static Shell & Glassmorphic DOM Hierarchy   │
│   ├── css/style.css ────── McLaren Orange Theme, Glassmorphism, Layout │
│   ├── js/app.js ────────── Reactive State Machine, Event Orchestrator  │
│   │    │                                                               │
│   │    ├── Vis-Network ──── Force-Directed Barnes-Hut Graph Canvas     │
│   │    ├── Chart.js ─────── Dynamic ORA, Scatter & Proximity Plots     │
│   │    └── Canvas Engine ── Background Particle Network Physics        │
│   │                                                                    │
│   └── data/*.json ──────── RESTful JSON Data Layer                     │
│        ├── subnetworks.json (Graph nodes, edges, expression, clusters) │
│        ├── pathways.json (Enrichr KEGG & Reactome ORA rankings)        │
│        ├── network_metrics.json (Centralities, hubs, Louvain modules)  │
│        ├── proximity.json (Guney dc null distribution & z-scores)      │
│        ├── gnn.json (GraphSAGE/GAE benchmarks, hypotheses, PubMed)     │
│        └── comparison.json (Menche separation, Jaccard, cross-talk)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack & Directory Structure

### 2.1 Technology Stack
- **Frontend Architecture**: Pure Vanilla JavaScript (ES6+), Semantic HTML5, CSS3 with Custom Properties (Variables).
- **Network Graph Rendering**: **vis-network.js v9.1.2** (Physics simulation via Barnes-Hut Quadtree algorithm, interactive pan/zoom, dynamic canvas camera focusing).
- **Statistical Charting**: **Chart.js v4.4.1 UMD** (Interactive bar charts, multi-omics Jaccard comparisons, 1,000-permutation histogram distributions, topological centrality scatter plots).
- **Background Effects**: Native HTML5 Canvas 2D Context Particle Engine with spatial distance-based edge joining.
- **Backend / Web Server**: `website/server.py` leveraging Python's `http.server.SimpleHTTPRequestHandler` with multithreaded request handling and cross-origin resource sharing headers.
- **Data Export Pipeline**: `scripts/export_web_data.py` (transforms NetworkX graphmls, PyTorch checkpoints, and pandas Parquet/CSV artifacts into optimized JSON).

### 2.2 Directory Structure
```
website/
├── index.html                   # Core single-page application structure & modals
├── server.py                    # Lightweight local web server (Port 8080)
├── css/
│   └── style.css                # Dark theme, glassmorphic styling, responsive grid
├── js/
│   └── app.js                   # State machine, event listeners, canvas & chart logic
├── vendor/
│   ├── vis-network.min.js       # Force-directed network visualization library
│   ├── vis-network.min.css      # Vis.js canvas stylesheets
│   ├── chart.umd.min.js         # Chart.js library
│   ├── gsap.min.js              # Animation utilities
│   └── confetti.min.js          # Canvas celebration effect
├── data/                        # Static JSON data endpoints
│   ├── subnetworks.json         # Extracted 2-hop & RWR subnetwork graphs
│   ├── pathways.json            # KEGG/Reactome pathway over-representation analysis
│   ├── network_metrics.json     # Degree, betweenness, eigenvector centralities
│   ├── proximity.json           # Guney closest-distance null permutation runs
│   ├── gnn.json                 # Inductive GraphSAGE, GAE & literature hypotheses
│   ├── comparison.json          # Menche separation s_AB & 2-hop cross-talk bridges
│   └── presentation.json        # 12-slide defense deck metadata
└── figures/                     # Publication-grade PNG charts and ROC/PR curves
```

---

## 3. Server Architecture (`website/server.py`)

The server is initiated by executing `python website/server.py`. It establishes a dedicated local HTTP daemon:

1. **Working Directory Anchoring**: Automatically resolves the directory of `server.py` as the root document path, preventing path traversal issues regardless of where the command is launched.
2. **Port Allocation & Fallback**: Binds by default to `http://localhost:8080`. If port 8080 is occupied, it systematically queries alternative ports (`8081`, `8082`, `8888`).
3. **MIME Type Handling**: Ensures proper headers for `.js` (`application/javascript`), `.css` (`text/css`), and `.json` (`application/json`), preventing CORS or script execution blocks.
4. **Browser Auto-Launch**: Spawns the default operating system browser directly to the application URL upon startup.

---

## 4. Frontend State Machine & Application Lifecycle (`website/js/app.js`)

The client application runs as an Immediately Invoked Function Expression (IIFE) to prevent global namespace pollution while maintaining an encapsulated reactive state object:

```javascript
const state = {
  // Explorer Datasets (loaded asynchronously via Promise.all)
  subnetworksData: null,
  pathwaysData: null,
  metricsData: null,
  proximityData: null,
  gnnData: null,
  comparisonData: null,
  
  // Subnetwork Canvas Filters
  selectedDrug: 'metformin',      // 'metformin' | 'imatinib'
  selectedMethod: 'rwr',          // 'rwr' | '2hop'
  selectedSizing: 'degree',       // 'degree' | 'betweenness' | 'eigenvector'
  edgeScoreThreshold: 700,        // Range: 700 to 950
  maxRenderedNodes: 120,          // Range: 30 to 250
  visNetwork: null,               // Vis.js Network instance
  physicsEnabled: true,           // Toggle Barnes-Hut solver
  
  // Pathway ORA Filters
  pathwayDrug: 'metformin',
  pathwayScope: 'rwr_subnetwork', // 'rwr_subnetwork' | '2hop_subnetwork' | 'lincs_perturbed'
  fdrThreshold: 0.05,             // Benjamini-Hochberg FDR cutoff
  chartPathways: null,            // Chart.js instance
  
  // Centrality Filters
  centDrug: 'metformin',
  chartCentrality: null,
  
  // Proximity Filters
  proxPair: 'metformin_t2d',      // 'metformin_t2d' | 'imatinib_cml' | controls
  chartProximity: null,
  
  // GNN Filters
  gnnDrug: 'metformin',
  chartJaccard: null
};
```

### Application Initialization Lifecycle:
1. **DOM Content Loaded (`DOMContentLoaded`)**:
   - Spawns the **Interactive Particle Background** on `<canvas id="bg-canvas">`.
   - Binds all DOM Event Listeners (tab switches, button pills, sliders, input search, modal dismissals).
   - Executes `loadAllData()` which concurrently fetches all 6 JSON endpoints via `Promise.all()`.
2. **Data Hydration**:
   - Once all JSON payloads resolve, `state` is hydrated.
   - The default tab (`Subnetwork Canvas`) is automatically rendered via `initSubnetworkCanvas()`.
3. **Lazy Rendering Strategy**:
   - Secondary tabs (Pathways, Centralities, Proximity, GNN, Comparison) instantiate their Chart.js canvases and populate tables only when the user first clicks on their respective tab. This ensures instantaneous page loads with zero lag.

---

## 5. Detailed Breakdown of Every Website Component & Feature

### 5.1 Interactive Particle Background (`#bg-canvas`)
- **How it works**: Uses HTML5 Canvas 2D context to simulate a living molecular interactome.
- **Physics Mechanism**: 
  - Initializes 60 floating particles with random Cartesian coordinates `(x, y)` and velocities `(vx, vy)`.
  - On every animation frame (`requestAnimationFrame`), calculates the Euclidean distance between all pairs: $d = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$.
  - If $d < 120\text{px}$, it renders a delicate connecting filament with dynamic opacity: $\alpha = 0.15 \times (1 - d/120)$.
  - Automatically recalculates dimensions on window resize events to maintain crisp rendering without stretching.

### 5.2 Top Navigation Header
- **Brand Logo & Title**: Displays the stylized PharmaPath interactome logo and platform badge.
- **Fullscreen Utility Button (`#btn-fullscreen`)**: Leverages the HTML5 Fullscreen API (`document.documentElement.requestFullscreen()`). Enables distraction-free scientific analysis during presentations or laboratory reviews.

---

### 5.3 Tab 1: Subnetwork Canvas (`#tab-subnetworks`)

This is the primary topological sandbox of the platform, rendering interactome neighborhoods in real-time.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left Control Sidebar (Glass Panel)   │  Right Canvas Viewport (Vis.js Quadtree)     │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  • Select Drug: [Metformin] [Imatinib]│  [Mini KPIs: Nodes | Edges | Density | Targets]│
│  • Algorithm: [RWR r=0.5] [2-Hop]    │                                              │
│  • Node Sizing: [Degree / Betweenness]│                (Star) Seed Targets           │
│  • Min Edge Score Slider (700 - 950)  │               /                              │
│  • Max Nodes Slider (30 - 250)        │          (Red)───(Blue)                      │
│  • Highlight Gene: [Input] [Search]   │            \     /                           │
│  • Action: [Pause Physics] [Center]   │            (Green) Up/Down Perturbed         │
│  • Color Aesthetic Legend             │  [Click Node to Inspect Multi-Omics Details] │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Underlying Mechanics of Tab 1 Controls:
1. **Drug Selector Pills (`data-drug`)**:
   - Switches between `metformin` and `imatinib`.
   - Triggers `initSubnetworkCanvas()`, loading the corresponding graph from `state.subnetworksData`.
2. **Extraction Algorithm Pills (`data-method`)**:
   - Switches between **Random Walk with Restart (RWR, $r=0.5$)** and **2-Hop Neighborhood**.
   - Dynamically recomputes the node set and edge list based on the chosen mathematical diffusion model.
3. **Node Sizing Dropdown (`#select-sizing-metric`)**:
   - **Degree Centrality**: Sets node radius proportional to local connection density: $r = \max(10, \min(30, 10 + 0.5 \times \text{degree}))$.
   - **Betweenness Centrality**: Scales nodes based on their role as communication bridges: $r = \max(10, \min(30, 10 + 0.8 \times \text{degree}))$.
   - Seed drug targets are consistently rendered with an amplified radius ($r = 26–28\text{px}$) to maintain visual prominence.
4. **Min STRING Edge Score Slider (`#slider-edge-score`)**:
   - Range: 700 (high-confidence minimum) to 950 (extreme physical certainty).
   - In real-time, filters out edges below the threshold: $e.\text{score} \ge \text{threshold}$.
   - Edge visual width scales dynamically with score: $\text{width} = \max(1, (\text{score} - 700) / 100)$.
5. **Max Rendered Nodes Slider (`#slider-max-nodes`)**:
   - Range: 30 to 250 nodes.
   - **Target-Preserving Pruning Algorithm**: If the graph contains more nodes than the slider limit, the algorithm separates nodes into `targets` and `non_targets`. It preserves **100% of seed drug targets**, sorts remaining neighbors by degree descending, and caps the total. This guarantees that drug targets are never pruned out.
6. **Gene Symbol Search (`#input-gene-search` & `#btn-gene-search`)**:
   - Case-insensitive search supporting Enter key or button click.
   - Queries the Vis.js internal dataset. If found, executes:
     - `visNetwork.selectNodes([geneSymbol])`
     - `visNetwork.focus(geneSymbol, { scale: 1.5, animation: { duration: 800 } })`
   - Spawns an animated toast notification confirming target location.
7. **Pause / Resume Physics Button (`#btn-toggle-physics`)**:
   - Toggles the Barnes-Hut quadtree force simulation on and off.
   - Freezes nodes in place once stabilized, allowing fluid user pan/zoom without node drift.
8. **Center View Button (`#btn-fit-canvas`)**:
   - Calls `visNetwork.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })`, auto-zooming and centering the entire subnetwork within the viewport.
9. **Mini KPI Bar (`#kpi-net-nodes`, etc.)**:
   - Dynamically displays: **Total Nodes**, **Total Edges**, **Graph Density** ($\frac{2|E|}{|V|(|V|-1)}$), and **Targets Captured**.
10. **Node Aesthetics & Color Encoding**:
    - ⭐ **Gold Star (`#F1C40F`)**: Seed Drug Target (direct biochemical binding target).
    - 🔴 **Red Node (`#E74C3C`)**: Up-regulated protein from LINCS L1000 perturbation ($z > +1.0$).
    - 🟢 **Green Node (`#2ECC71`)**: Down-regulated protein from LINCS L1000 perturbation ($z < -1.0$).
    - 🔵 **Blue Node (`#3498DB`)**: Interactome neighbor mediating network communication.
11. **Node Inspection Modal (`#node-modal`)**:
    - Clicking any node triggers `openNodeModal(node)`.
    - Opens a glassmorphic overlay detailing: Gene Symbol, Functional Role, Subnetwork Degree, LINCS Expression Z-Score, Community Cluster ID, and a live PubMed direct link button (`https://pubmed.ncbi.nlm.nih.gov/?term={drug}+AND+{gene}`).

---

### 5.4 Tab 2: Pathways & Over-Representation Analysis (`#tab-pathways`)

Provides statistical pathway validation against the KEGG 2021 Human and Reactome 2022 ontologies.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left: Biological Sanity & Filters    │  Right: Pathway Visualization & Rankings     │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  • Metformin Sanity Card [PASSED]     │  Horizontal Bar Chart: -log10(Adj. P-Value)  │
│    (AMPK, mTOR, FoxO, Complex I)      │  ┌────────────────────────────────────────┐  │
│  • Imatinib Sanity Card [PASSED]      │  │ Complex I Biogenesis ████████████ 1e-142│  │
│    (RTK, SCF-KIT, BCR-ABL, CML)       │  │ Oxidative Phospho    ████████████ 1e-153│  │
│                                       │  │ AMPK Signaling       █████ 3.6e-5       │  │
│  • Drug: [Metformin] [Imatinib]       │  └────────────────────────────────────────┘  │
│  • Scope: [RWR] [2-Hop] [LINCS]       │                                              │
│  • FDR Threshold Slider (0.001 - 0.10)│  Interactive Ranking Table:                  │
│                                       │  [Term | Database | Adj. P-Val | Overlap]    │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Components & Data Flow:
1. **Biological Sanity Audit Cards**:
   - Directly loaded from `pathways.json -> sanity_audit`.
   - Displays real-time validation badges (`SANITY PASSED` in emerald green).
   - Lists matched biological hallmark keywords (e.g., `AMPK`, `mTOR`, `glycolysis`, `tyrosine kinase`, `leukemia`).
2. **Scope Selector Pills (`data-pscope`)**:
   - `rwr_subnetwork`: Pathways enriched in the high-affinity stationary distribution.
   - `2hop_subnetwork`: Broad multi-pathway interactome neighborhood.
   - `lincs_perturbed`: Pathways enriched strictly among experimentally up/down-regulated genes.
3. **FDR Threshold Slider (`#slider-fdr-thresh`)**:
   - Dynamically filters out pathways exceeding the selected Benjamini-Hochberg False Discovery Rate ($q > \text{threshold}$).
4. **Horizontal Bar Chart (`#chart-pathways`)**:
   - Plots the top 8 most statistically significant pathways.
   - X-Axis represents $-\log_{10}(p_{\text{adj}})$, transforming tiny p-values (e.g., $1.26 \times 10^{-153}$) into intuitive positive bars.
5. **Pathway Ranking Table (`#table-pathways`)**:
   - Displays Term Name, Source Database badge (KEGG vs Reactome), Adjusted P-Value formatted in scientific notation ($3.65 \times 10^{-5}$), Gene Overlap ratio (e.g., `38/120`), and Enrichr Combined Score ($c = \ln(p) \times z$).

---

### 5.5 Tab 3: Centrality & Hubs (`#tab-centralities`)

Exposes the topological hierarchy of the perturbed interactome to pinpoint critical information bottlenecks and hub proteins.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left: Topological Scatter Plot       │  Right: Community & Bottleneck Tables        │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  Degree Centrality (X) vs             │  Louvain Modularity Clusters Table:          │
│  Betweenness Centrality (Y)           │  • Cluster 0: Complex I Biogenesis (39 genes)│
│                                       │  • Cluster 1: Respiratory Transport (35)     │
│   Betweenness                         │  • Cluster 2: Oxidative Phosphorylation (33) │
│       ▲       ● Dual Bridge (Purple)  │                                              │
│       │    ● Bottleneck (Red)         │  Top Bottleneck Bridges Table:               │
│       │  ● Standard   ● Hub (Orange)  │  • NDUFA12: Deg=52, Betweenness=0.0642       │
│       └────────────────────────►      │  • NDUFA9:  Deg=48, Betweenness=0.0451       │
│              Raw Degree               │  • PRKAA1:  Deg=38, Betweenness=0.0418       │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Components & Data Flow:
1. **Interactive Centrality Scatter Plot (`#chart-centrality-scatter`)**:
   - X-Axis: Raw Degree Centrality ($k = \text{number of interactome neighbors}$).
   - Y-Axis: Betweenness Centrality ($C_B = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$).
   - **Quad-Color Topological Classification**:
     - 🟣 **Dual Bridge (`#9B59B6`)**: Top 5% in BOTH degree and betweenness (master regulators).
     - 🟠 **Hub (`#FF8000`)**: Top 5% in degree (local communication cluster centers).
     - 🔴 **Bottleneck (`#E74C3C`)**: Top 5% in betweenness (inter-modular informational bridges).
     - 🔵 **Standard Node (`#3498DB`)**: Peripheral subnetwork components.
   - Interactive Tooltip: Displays exact gene symbol, degree count, and betweenness score on mouse hover.
2. **Louvain Modularity Table (`#table-communities`)**:
   - Displays community clusters discovered by optimizing Newman-Girvan modularity:
     $$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$
   - Details Cluster ID, protein member count, and dominant biological pathway annotation.
3. **Top Bottleneck Bridges Table (`#table-bottlenecks`)**:
   - Sorts subnetwork proteins by betweenness centrality descending.
   - Reports Gene Symbol, Degree, Betweenness, Eigenvector Centrality, and Functional Role badge.

---

### 5.6 Tab 4: Disease Proximity Lab (`#tab-proximity`)

Implements the canonical **Guney et al. (2016 Nature Communications)** network proximity metric to test whether drug targets localize closer to disease modules than expected by chance.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left: 1,000-Permutation Histogram    │  Right: Proximity Benchmark Summary & Theory │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  Pair Selector:                       │  Benchmark Summary Table:                    │
│  [Metformin → T2D (Primary)]          │  • Metformin → T2D: dc=0.213, z=-18.28 (PROX)│
│                                       │  • Imatinib  → CML: dc=0.400, z=-7.25  (PROX)│
│  Null Distribution vs Observed        │  • Metformin → CML: dc=1.951, z=+18.32 (DIST)│
│    Frequency                          │  • Imatinib  → T2D: dc=1.300, z=+1.18  (DIST)│
│        ▲      Null (Blue, mean=1.012) │                                              │
│        │        ████                  │  Mathematical Callout:                       │
│        │      ████████                │  ⟨dc(T, S)⟩ = (1/|T|) ∑ min d(t, s)          │
│        │  █   ████████                │                                              │
│        └──┴─────────────────────►     │  Negative z-score (z ≤ -2.0) indicates       │
│         Obs=0.213 (Orange)  dc        │  statistically significant proximity.        │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Components & Data Flow:
1. **Drug-Disease Pair Selector (`#select-prox-pair`)**:
   - Allows instant switching between primary therapeutic pairs and reciprocal negative controls:
     - `metformin_t2d`: Primary Metformin therapeutic hypothesis.
     - `imatinib_cml`: Primary Imatinib therapeutic hypothesis.
     - `metformin_cml`: Negative control (Metformin evaluated on leukemia genetics).
     - `imatinib_t2d`: Negative control (Imatinib evaluated on metabolic diabetes genetics).
2. **Degree-Preserving Null Distribution Histogram (`#chart-proximity-dist`)**:
   - Renders the distribution of $d_c$ across **1,000 random node sets** matching the exact degree distribution of the drug targets.
   - Renders the observed distance $d_c$ as a distinct high-contrast McLaren Orange vertical bar.
   - Visualizes the massive gap between random expectation ($\mu_{null} = 1.012$) and observed reality ($d_c = 0.213$).
3. **Statistical KPI Callout Card (`#prox-stats-callout`)**:
   - Shows Observed $\langle d_c \rangle$, Null Mean $\pm$ Standard Deviation, and Proximity Z-score ($z = \frac{d_c - \mu_{null}}{\sigma_{null}}$).
   - Green text highlighting for statistically proximate pairs ($z \le -2.0$); red highlighting for non-proximate negative controls.
4. **Benchmark Summary Table (`#table-proximity-summary`)**:
   - Compares all four test runs side-by-side with empirical p-values ($p = \frac{1}{N} \sum \mathbb{I}(d_{null} \le d_c)$).
5. **Mathematical Theory Card**:
   - Formats the Guney closest-distance equation and explains how degree-preserving permutations eradicate interactome ascertainment bias.

---

### 5.7 Tab 5: GNN Link Predictions Studio (`#tab-gnn`)

Exposes the machine learning link prediction benchmark, zero-leakage protocol, target recovery, and 20 computational repurposing hypotheses.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left: GNN Benchmark & Leakage Audit  │  Right: Top-20 Candidate Hypotheses          │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  Model Architecture Benchmark:        │  Drug Selector: [Metformin] [Imatinib]       │
│  • GraphSAGE: AUROC = 0.8865, AP = 0.9008                                            │
│  • GAE:       AUROC = 0.8832, AP = 0.8958    Top-20 Ranking Table:                   │
│  • Node2Vec:  AUROC = 0.5000, AP = 0.5000    • #1 NDC80   (1.0000) [Kinetochore] [PM]│
│                                       │      • #2 UQCR11  (0.9999) [Complex III] [PM]│
│  Leave-Targets-Out Cross-Validation:  │      • #3 PMPCB   (0.9999) [Peptidase]   [PM]│
│  • Metformin: NDUFS7 ranked #15 / 15k │      • #4 UQCRH   (0.9999) [Complex III] [PM]│
│    Hits@20 = 50.0%, MRR = 0.0334      │      • #5 KIF2C   (0.9999) [Spindle]     [PM]│
│  • Imatinib:  CSF1R  ranked #85 / 15k │                                              │
│    Hits@100 = 50.0%, MRR = 0.0059     │  Methodological Callout:                     │
│                                       │  Predictions represent topological           │
│  Embedded Publication Curves:         │  hypotheses, NOT biochemical binding proof.  │
│  [ROC & PR Curves Preview Image]      │                                              │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Components & Data Flow:
1. **Model Architecture Benchmark Table (`#table-gnn-metrics`)**:
   - Displays inductive performance on 23,671 held-out test edges.
   - Highlights GraphSAGE's superiority ($\text{AUROC} = 0.8865, \text{AP} = 0.9008$) and GAE ($\text{AUROC} = 0.8832$) over the baseline ($\text{AUROC} = 0.5000$).
2. **Leave-Targets-Out Recovery Table (`#table-gnn-recovery`)**:
   - Documents the recovery of hidden test targets removed prior to embedding computation.
   - Reports Hidden Target Names, Recovered Rank across the entire 15,882-protein proteome, Mean Reciprocal Rank (MRR), and Hits@20.
3. **Publication Curve Preview (`#img-gnn-curves`)**:
   - Embeds high-resolution ROC and Precision-Recall plots directly from `website/figures/gnn_link_prediction_roc_pr.png`.
4. **Top-20 Novel Candidate Hypotheses Table (`#table-gnn-hypotheses`)**:
   - Dynamically filtered by drug selection pills (`metformin` vs `imatinib`).
   - Reports: Candidate Gene Symbol, GraphSAGE Prediction Confidence, Biological Interactome Context, Status Badge, and an interactive **PubMed Query Button**.
   - Clicking the PubMed button launches an active literature search: `https://pubmed.ncbi.nlm.nih.gov/?term={drug}+AND+{gene}`.
5. **Rigor & Disclaimer Notice**:
   - Clearly states that link predictions represent interactomic and functional topological hypotheses, not direct biochemical binding affinity.

---

### 5.8 Tab 6: Two-Drug Comparison & Synergy Lab (`#tab-comparison`)

Compares Metformin and Imatinib across all omics layers, computing interactome separation and identifying shared cross-talk proteins for combination therapy.

```
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│  Left: Separation & Jaccard Overlap   │  Right: Shared Cross-Talk & Synergy Rationale│
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│  Interactome Overlap Summary Table:   │  Shared Cross-Talk Hubs Table (347 Shared):  │
│  • Seed Targets:    Jaccard = 0.0000  │  • AKT1: Full Deg=738, Shared Hub=YES        │
│  • 2-Hop Network:   Jaccard = 0.5314  │  • TP53: Full Deg=1126, Shared Hub=YES       │
│  • RWR Subnetwork:  Jaccard = 0.0274  │  • MAPK1:Full Deg=582, Shared Hub=YES        │
│  • LINCS Perturbed: Jaccard = 0.0076  │  • STAT3:Full Deg=485, Shared Hub=YES        │
│                                       │                                              │
│  Menche Separation KPI Cards:         │  Combination Pharmacology Report:            │
│  • Separation sAB = +1.3503           │  • Eradication of Quiescent Leukemic Stem    │
│  • Inter-Distance ⟨dAB⟩ = 2.409       │    Cells (LSCs) via Complex I inhibition.    │
│  • State: Distinct Modules (s > 0)    │  • Cardioprotective AMPK signaling mitigating│
│                                       │    Imatinib-induced myocardial stress.       │
│  Multi-Omics Jaccard Bar Chart        │                                              │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

#### Components & Data Flow:
1. **Multi-Omics Jaccard Overlap Table (`#table-comp-summary`)**:
   - Quantifies intersection over union across seed targets ($J=0.0000$), RWR subnetworks ($J=0.0274$), 2-hop neighborhoods ($J=0.5314$), and LINCS perturbed transcriptomics ($J=0.0076$).
2. **Menche Separation KPI Cards (`s_AB`)**:
   - Implements Menche et al. (2015 Science) interactome separation:
     $$s_{AB} = \langle d_{AB} \rangle - \frac{\langle d_{AA} \rangle + \langle d_{BB} \rangle}{2}$$
   - Displays $s_{AB} = +1.3503$, confirming that the direct target modules are topologically segregated in distinct interactome niches.
3. **Multi-Omics Jaccard Horizontal Bar Chart (`#chart-comp-jaccard`)**:
   - Visualizes Jaccard indices across all analytical dimensions.
4. **Shared Cross-Talk Hubs Table (`#table-shared-proteins`)**:
   - Lists the 347 proteins present in both 2-hop interactome neighborhoods.
   - Identifies the 22 shared topological hubs (e.g., AKT1, TP53, MAPK1, STAT3, SRC) and shared bottleneck bridges.
5. **Combination Pharmacology Markdown Report (`#combination-report-box`)**:
   - Renders formatted clinical rationale detailing how Metformin forces quiescent leukemic stem cells (LSCs) out of dormancy to overcome Imatinib resistance in CML.

---

## 6. Data Ingestion & Transformation Pipeline (`export_web_data.py`)

The website does not query heavy graph databases at runtime. Instead, `scripts/export_web_data.py` compiles all analytical findings from `data/processed/` and `results/` into clean, lightweight JSON files:

```
[data/processed/subnetwork_*.graphml] ────► export_subnetworks() ────► website/data/subnetworks.json
[results/tables/pathways_*.csv]        ────► export_pathways()    ────► website/data/pathways.json
[results/tables/centrality_*.csv]      ────► export_network_metrics() ► website/data/network_metrics.json
[results/tables/proximity_*.json]      ────► export_proximity()   ────► website/data/proximity.json
[results/tables/gnn_*.csv]             ────► export_gnn()         ────► website/data/gnn.json
[results/tables/comparison_*.csv]      ────► export_comparison()  ────► website/data/comparison.json
```

### JSON Schema Highlights:
- **`subnetworks.json`**: Graph nodes contain `id`, `label`, `is_target`, `expression_z`, `degree`, and `community_id`. Edges contain `from`, `to`, `score`, and `weight`.
- **`pathways.json`**: Contains library-tagged pathway records (`KEGG_2021_Human`, `Reactome_2022`), p-values, adjusted p-values, odds ratios, and combined scores.
- **`proximity.json`**: Houses empirical null distribution arrays ($1,000$ values each) alongside observed closest distances and z-scores.
- **`gnn.json`**: Structures GNN test benchmarks, leave-targets-out recovery statistics, and top-20 hypotheses with biological annotations.
- **`comparison.json`**: Stores Jaccard overlap matrices, Menche separation variables, shared cross-talk protein metrics, and clinical combination reports.

---

## 7. Automated Testing & Verification Suite (`test_website_playwright.py`)

PharmaPath includes a full end-to-end automated browser verification suite powered by Playwright:

1. **Headless Browser Execution**: Launches a Chromium instance at $1600 \times 950$ viewport with high-DPI scaling ($1.5\times$).
2. **Zero-Error Console & Page Monitoring**: Binds listeners to intercept any `console.error` or unhandled JavaScript `pageerror`. Any error immediately fails the test.
3. **Comprehensive Component Exercising**:
   - Traverses every tab in sequential order.
   - Clicks drug switches, method toggles, and sizing dropdowns.
   - Dispatches slider input events across edge score and max node thresholds.
   - Executes gene symbol searches (`ABL1`, `PRKAA1`).
   - Simulates node clicks on the Vis.js canvas and verifies modal popup appearance and dismissal.
   - Captures high-resolution validation screenshots saved directly into `reports/screenshots/`.
4. **Execution Command**:
   ```bash
   python scripts/test_website_playwright.py
   ```

---

## 8. Summary of Architectural Advantages

1. **Sub-Second Latency**: Pre-computed multi-omics JSON architecture allows instantaneous rendering without backend graph query lag.
2. **Zero Data Leakage Integrity**: Graph neural network visualizations reflect strict inductive separation with held-out edge validation.
3. **Interactive Explainability**: Every score, badge, and curve is directly traceable to canonical formulas (Guney $d_c$, Menche $s_{AB}$, Newman Modularity $Q$) and literature citations.
4. **Resilient Offline Operation**: The web application requires no external cloud APIs or internet connection to render its complete research suite.
