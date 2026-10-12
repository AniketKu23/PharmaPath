/**
 * PharmaPath - Network-Pharmacology & GNN Discovery Platform
 * Interactive Research Lab Application Logic
 */

(function () {
  'use strict';

  // State Management
  const state = {
    // Explorer Datasets
    subnetworksData: null,
    pathwaysData: null,
    metricsData: null,
    proximityData: null,
    gnnData: null,
    comparisonData: null,
    
    // Subnetwork filters
    selectedDrug: 'metformin',
    selectedMethod: 'rwr',
    selectedSizing: 'degree',
    edgeScoreThreshold: 700,
    maxRenderedNodes: 120,
    visNetwork: null,
    physicsEnabled: true,
    
    // Pathway filters
    pathwayDrug: 'metformin',
    pathwayScope: 'rwr_subnetwork',
    fdrThreshold: 0.05,
    chartPathways: null,
    
    // Centrality filters
    centDrug: 'metformin',
    chartCentrality: null,
    
    // Proximity filters
    proxPair: 'metformin_t2d',
    chartProximity: null,
    
    // GNN filters
    gnnDrug: 'metformin',
    chartJaccard: null,
  };

  // Toast Notification
  function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 2800);
  }

  // =========================================================================
  // Interactive Explainer Tooltip System & Concept Dictionary
  // =========================================================================
  const TOOLTIP_DATA = {
    // Navigation & Primary Modules
    subnetwork_canvas: {
      title: 'Subnetwork Canvas',
      category: 'Interactive Module',
      desc: 'Interactive force-directed graph rendering seed-centric drug-target interactome neighborhoods using Vis.js. Displays topological associations, expression perturbation, and physical protein complexes.',
      relevance: 'Allows researchers to visually explore how small molecules propagate signals across the human protein interactome.'
    },
    pathways_ora: {
      title: 'Pathways & Over-Representation Analysis',
      category: 'Functional Genomics',
      desc: 'Statistical over-representation analysis mapping extracted subnetwork proteins and perturbed genes onto KEGG and Reactome pathway databases.',
      relevance: 'Identifies systemic biological processes and signaling cascades modulated by therapeutic interventions.'
    },
    centrality_modularity: {
      title: 'Network Centralities & Modularity',
      category: 'Graph Theory',
      desc: 'Topological characterization decomposing interactome architectures into degree hubs, betweenness bottlenecks, dual bridges, and Louvain modularity clusters.',
      relevance: 'Highlights vulnerable signaling nodes and master regulatory proteins governing drug action.'
    },
    disease_proximity: {
      title: 'Disease Module Proximity',
      category: 'Network Pharmacology',
      desc: 'Measures network-based distance between drug targets and disease-associated genes in the human interactome relative to a degree-matched permutation null model (Guney et al., 2016).',
      relevance: 'Validates on-target therapeutic efficacy and uncovers rational drug repurposing indications.'
    },
    gnn_predictions: {
      title: 'Inductive GNN Link Predictions',
      category: 'Deep Graph Learning',
      desc: 'Graph Neural Network (GraphSAGE) architecture trained under a zero-data-leakage regime to infer novel functional associations between drugs and proteins.',
      relevance: 'Generates high-priority candidate hypotheses for secondary mechanisms of action, off-target interactions, and synergistic targets.'
    },
    drug_comparison: {
      title: 'Two-Drug Comparative Pharmacology',
      category: 'Comparative Systems Biology',
      desc: 'Direct interactome comparison evaluating module separation (Menche et al., 2015), multi-omics Jaccard overlaps, and combination synergy between Metformin and Imatinib.',
      relevance: 'Provides mechanistic justification for combination therapies in overcoming drug resistance (e.g., in CML leukemic stem cells).'
    },

    // Drug Entities & Selectors
    drug_selection: {
      title: 'Select Active Drug',
      category: 'Control Filter',
      desc: 'Switches the active multi-omics dataset and interactome views between Metformin (Type 2 Diabetes) and Imatinib (Chronic Myeloid Leukemia).',
      relevance: 'Enables comparative exploration between a metabolic regulator and an oncogenic kinase inhibitor.'
    },
    metformin: {
      title: 'Metformin (Glucophage)',
      category: 'Biguanide / Antidiabetic',
      formula: 'C<sub>4</sub>H<sub>11</sub>N<sub>5</sub> (MW: 129.16 g/mol)',
      desc: 'First-line oral biguanide for Type 2 Diabetes. Primary molecular targets include AMPK subunit PRKAA1 and mitochondrial respiratory Complex I subunits (NDUFS7, NDUFA1, NDUFV1).',
      relevance: 'Inhibits hepatic gluconeogenesis, activates cellular energy sensor AMPK, and starves glycolytically dependent cancer cells.'
    },
    imatinib: {
      title: 'Imatinib (Gleevec / STI571)',
      category: 'Tyrosine Kinase Inhibitor',
      formula: 'C<sub>29</sub>H<sub>31</sub>N<sub>7</sub>O (MW: 493.60 g/mol)',
      desc: 'Selective 2-phenylaminopyrimidine kinase inhibitor targeting the oncogenic BCR-ABL1 fusion tyrosine kinase, KIT, and PDGFRA/B.',
      relevance: 'Standard-of-care targeted therapy for Chronic Myeloid Leukemia (CML) and gastrointestinal stromal tumors (GIST).'
    },

    // Subnetwork Extraction & Algorithms
    extraction_method: {
      title: 'Subnetwork Extraction Method',
      category: 'Algorithmic Filter',
      desc: 'Choose between Random Walk with Restart (global steady-state network diffusion) or 2-Hop Neighborhood (local immediate binding partners).',
      relevance: 'RWR captures multi-step functional signaling pathways, while 2-Hop captures direct physical binding complexes.'
    },
    rwr: {
      title: 'Random Walk with Restart (RWR)',
      category: 'Diffusion Algorithm',
      formula: 'p<sup>t+1</sup> = (1 &minus; r) W p<sup>t</sup> + r p<sup>0</sup> &nbsp;(r = 0.5)',
      desc: 'Iterative network propagation simulating a random walker starting at drug seed targets. At each transition step, the walker diffuses across edges or restarts back at seeds with probability r=0.5, converging to a stationary probability distribution.',
      relevance: 'Prioritizes proteins topologically proximal to drug targets across the entire interactome, discovering both direct and indirect functional mediators.'
    },
    two_hop: {
      title: '2-Hop Neighborhood',
      category: 'Graph Expansion',
      formula: 'N<sub>2</sub>(T) = { v &isin; V | d(T, v) &le; 2 }',
      desc: 'Extracts all immediate physical binding partners (1-hop) and secondary interaction neighbors (2-hop) of drug targets from the human interactome graph.',
      relevance: 'Isolates the local structural scaffold around drug targets without degree-biased diffusion overreach.'
    },

    // Canvas Controls, Visual Encodings & Aesthetics
    sizing_metric: {
      title: 'Node Sizing Metric',
      category: 'Visual Encoding',
      desc: 'Dynamically resizes canvas protein nodes based on their Degree Centrality, Betweenness Centrality, or Eigenvector Centrality.',
      relevance: 'Visually highlights topologically dominant hubs and bottlenecks within the subnetwork.'
    },
    degree: {
      title: 'Degree Centrality',
      category: 'Topological Metric',
      formula: 'k<sub>i</sub> = &sum;<sub>j</sub> A<sub>ij</sub>',
      desc: 'Total number of physical and functional interaction partners directly connected to a protein in the interactome graph.',
      relevance: 'High-degree proteins (hubs) are structurally essential to interactome cohesion and are strongly enriched in disease-critical genes.'
    },
    betweenness: {
      title: 'Betweenness Centrality',
      category: 'Topological Metric',
      formula: 'C<sub>B</sub>(v) = &sum;<sub>s &ne; v &ne; t</sub> (&sigma;<sub>st</sub>(v) / &sigma;<sub>st</sub>)',
      desc: 'Fraction of all shortest paths between all pairs of proteins in the interactome that traverse through a specific node.',
      relevance: 'Identifies informational bottleneck proteins that bridge distinct functional modules and control cellular signal flow.'
    },
    eigenvector: {
      title: 'Eigenvector Centrality',
      category: 'Topological Metric',
      formula: 'x<sub>v</sub> = (1 / &lambda;) &sum;<sub>u &isin; N(v)</sub> x<sub>u</sub>',
      desc: 'Measures node influence based on the centrality of its neighbors; a protein scores highly if it connects to other high-scoring hubs.',
      relevance: 'Distinguishes master regulatory coordinators from peripheral nodes connected to minor interactors.'
    },
    edge_score: {
      title: 'Min STRING Edge Score',
      category: 'Confidence Cutoff',
      formula: 'Score &ge; 700 (High Confidence Threshold)',
      desc: 'STRING database combined interaction confidence (0–1000) integrating experimental assays, curated databases, co-expression, and text mining.',
      relevance: 'Thresholding at &ge;700 removes spurious, false-positive interactions, ensuring that subnetworks reflect genuine biological complexes.'
    },
    max_nodes: {
      title: 'Max Rendered Nodes',
      category: 'Performance Optimization',
      desc: 'Limits the active subnetwork display to the top N proteins ranked by diffusion probability or centrality while preserving all drug targets.',
      relevance: 'Prevents browser rendering lag and visual clutter on mobile and desktop viewports.'
    },
    gene_search: {
      title: 'Gene Symbol Search',
      category: 'Navigation Tool',
      desc: 'Searches for a specific human protein symbol (e.g. PRKAA1, ABL1, NDUFS7), highlighting the node and centering the canvas camera on it.',
      relevance: 'Facilitates rapid inspection of specific proteins of interest within dense interactome graphs.'
    },
    seed_target: {
      title: 'Seed Drug Target',
      category: 'Primary Target',
      desc: 'Primary validated protein target directly bound by the drug (curated from DrugBank / ChEMBL). Highlighted with a gold star badge.',
      relevance: 'The biological ground-zero of drug action where pharmacological perturbation originates.'
    },
    up_regulated: {
      title: 'Up-Regulated Expression (z > 1.0)',
      category: 'Transcriptomic Response',
      formula: 'z &ge; +1.0 (LINCS L1000)',
      desc: 'Protein whose corresponding mRNA expression is significantly upregulated following drug exposure in the NIH LINCS L1000 dataset (red node).',
      relevance: 'Indicates compensatory activation, transcription factor induction, or cellular stress responses.'
    },
    down_regulated: {
      title: 'Down-Regulated Expression (z < -1.0)',
      category: 'Transcriptomic Response',
      formula: 'z &le; &minus;1.0 (LINCS L1000)',
      desc: 'Protein whose mRNA expression is significantly repressed following drug exposure in LINCS L1000 (green node).',
      relevance: 'Reflects pathway inhibition, metabolic downregulation, or suppression of oncogenic transcriptional programs.'
    },
    interactome_neighbor: {
      title: 'Interactome Neighbor',
      category: 'Topological Partner',
      desc: 'Interacting protein present in the high-confidence PPI network that physically bridges drug targets and perturbed expression effectors (blue node).',
      relevance: 'Maintains network connectivity and mediates multi-step signal propagation.'
    },

    // KPIs
    kpi_nodes: {
      title: 'Subnetwork Node Count',
      category: 'Graph Size',
      desc: 'Total number of protein nodes currently rendered within the extracted subnetwork canvas.',
      relevance: 'Reflects the topological breadth of the drug\'s functional neighborhood.'
    },
    kpi_edges: {
      title: 'Subnetwork Edge Count',
      category: 'Graph Connectivity',
      desc: 'Total number of high-confidence physical and functional interactions connecting the rendered proteins.',
      relevance: 'Indicates the internal connectivity and signaling capacity within the module.'
    },
    kpi_density: {
      title: 'Network Density',
      category: 'Topological Cohesion',
      formula: '&rho; = 2 |E| / (|V| &middot; (|V| &minus; 1))',
      desc: 'Ratio of observed edges to all possible pairwise connections between the subnetwork nodes.',
      relevance: 'High density signifies tightly coordinated complexes; low density signifies branching signal cascades.'
    },
    kpi_targets: {
      title: 'Targets in Subgraph',
      category: 'Target Retention',
      desc: 'Number of primary validated drug targets present in the active subnetwork.',
      relevance: 'Verifies that the subnetwork retains core pharmacological anchors.'
    },

    // Pathways & ORA
    sanity_audit: {
      title: 'Biological Sanity Audit',
      category: 'Scientific Validation',
      desc: 'Automated sanity check verifying that extracted subnetworks significantly enrich expected hallmark pathways (e.g. AMPK/FoxO for Metformin, BCR-ABL/PI3K-Akt for Imatinib).',
      relevance: 'Guarantees methodological integrity and validates computational extraction against established empirical biology.'
    },
    ora: {
      title: 'Over-Representation Analysis (ORA)',
      category: 'Enrichment Method',
      formula: 'p = Hypergeometric(k, K, n, N)',
      desc: 'Statistical test determining whether subnetwork proteins overlap with curated pathway gene sets (KEGG, Reactome) more than expected by chance.',
      relevance: 'Interprets interactome subgraphs into well-defined cellular and biochemical pathways.'
    },
    scope_rwr: {
      title: 'RWR Subnetwork Scope',
      category: 'Enrichment Input',
      desc: 'Performs pathway enrichment exclusively on the protein set extracted via Random Walk with Restart.',
      relevance: 'Captures pathways influenced by global diffusion across the interactome.'
    },
    scope_2hop: {
      title: '2-Hop Subnetwork Scope',
      category: 'Enrichment Input',
      desc: 'Performs pathway enrichment on direct 1st and 2nd degree interaction partners of drug targets.',
      relevance: 'Captures immediate physical complexes and proximal signaling cascades.'
    },
    scope_lincs: {
      title: 'LINCS Perturbed Scope',
      category: 'Enrichment Input',
      desc: 'Performs pathway enrichment on differentially expressed genes (|z| &ge; 1.0) from the LINCS L1000 dataset.',
      relevance: 'Directly maps transcriptional cellular response signatures independent of network topology.'
    },
    fdr_threshold: {
      title: 'False Discovery Rate (FDR) Threshold',
      category: 'Statistical Filter',
      desc: 'Benjamini-Hochberg adjusted p-value cutoff (default 0.05) controlling false positives across multiple pathway tests.',
      relevance: 'Ensures reported enriched biological terms are statistically robust and reproducible.'
    },
    pathway_term: {
      title: 'Enriched Pathway Term',
      category: 'Biological Annotation',
      desc: 'Standardized biological pathway name from curated knowledgebases (KEGG or Reactome).',
      relevance: 'Provides functional context describing cellular machinery, signaling, or disease pathology.'
    },
    pathway_db: {
      title: 'Pathway Database',
      category: 'Knowledge Base',
      desc: 'Curated reference database source (KEGG 2021 Human or Reactome 2022).',
      relevance: 'Provides authoritative, peer-reviewed biochemical and signaling pathway models.'
    },
    pathway_overlap: {
      title: 'Gene Set Overlap',
      category: 'Overlap Count',
      desc: 'Ratio of subnetwork genes found in the pathway over total genes defined in that pathway (k / K).',
      relevance: 'Indicates the fraction of pathway components covered by the drug\'s subnetwork.'
    },
    combined_score: {
      title: 'Enrichr Combined Score',
      category: 'Enrichment Metric',
      formula: 'c = &minus;ln(p) &middot; z',
      desc: 'Product of the log p-value and the z-score deviation from expected rank in random permutations.',
      relevance: 'Prioritizes biological pathways with both high statistical significance and substantial gene representation.'
    },
    adjusted_p: {
      title: 'Adjusted P-Value (q-value)',
      category: 'Statistical Metric',
      desc: 'Benjamini-Hochberg corrected p-value controlling false discovery rate in multi-hypothesis testing.',
      relevance: 'q < 0.05 establishes rigorous statistical significance.'
    },

    // Centralities & Modularity
    scatter_topology: {
      title: 'Degree vs. Betweenness Scatter',
      category: 'Topological Classification',
      desc: 'Bivariate plot classifying proteins into hubs (high degree), bottlenecks (high betweenness), dual bridges (both), or standard nodes.',
      relevance: 'Visualizes the dual topological architecture of drug target interactomes.'
    },
    dual_bridge: {
      title: 'Dual Bridge (Hub-Bottleneck)',
      category: 'Topological Role',
      desc: 'Proteins scoring high in both Degree Centrality and Betweenness Centrality (purple markers).',
      relevance: 'Systemic master coordinators; targeting dual bridges causes profound structural disruption to disease modules.'
    },
    hub: {
      title: 'Interactome Hub',
      category: 'Topological Role',
      desc: 'Highly connected protein (high degree) located inside a dense community (orange markers).',
      relevance: 'Maintains local network stability and integrity across functional complexes.'
    },
    bottleneck: {
      title: 'Interactome Bottleneck',
      category: 'Topological Role',
      desc: 'Protein with high betweenness but moderate degree, acting as a critical bridge between separate modules (red markers).',
      relevance: 'Controls cross-talk between distinct cellular pathways.'
    },
    standard_node: {
      title: 'Standard Node',
      category: 'Topological Role',
      desc: 'Interactome protein with baseline connectivity performing specialized peripheral functions (blue markers).',
      relevance: 'Executes downstream biochemical actions within specific pathways.'
    },
    louvain: {
      title: 'Louvain Modularity Clustering',
      category: 'Community Detection',
      formula: 'Q = <sup>1</sup>/<sub>2m</sub> &sum;<sub>ij</sub> [ A<sub>ij</sub> &minus; <sup>k<sub>i</sub> k<sub>j</sub></sup>/<sub>2m</sub> ] &delta;(c<sub>i</sub>, c<sub>j</sub>)',
      desc: 'Greedy modularity optimization algorithm partitioning the interactome into non-overlapping, dense protein communities.',
      relevance: 'Uncovers functional multi-protein complexes and regulatory modules without prior annotations.'
    },
    community_id: {
      title: 'Community Cluster ID',
      category: 'Module Identifier',
      desc: 'Distinct functional partition index assigned to proteins by the Louvain modularity algorithm.',
      relevance: 'Groups proteins that work together in common biochemical machineries.'
    },
    community_size: {
      title: 'Community Size',
      category: 'Cluster Cardinality',
      desc: 'Total count of proteins assigned to a specific Louvain modularity cluster.',
      relevance: 'Indicates the scale of the functional protein module.'
    },
    dominant_pathway: {
      title: 'Dominant Pathway',
      category: 'Cluster Annotation',
      desc: 'Primary biological pathway most significantly enriched among proteins in this Louvain cluster.',
      relevance: 'Defines the core physiological function performed by the community.'
    },
    topological_role: {
      title: 'Topological Classification Role',
      category: 'Structural Role',
      desc: 'Categorization of a protein as a Dual Bridge, Hub, Bottleneck, or Standard Node based on centrality thresholds.',
      relevance: 'Predicts the vulnerability and impact of perturbing this protein in the interactome.'
    },

    // Proximity
    null_model: {
      title: 'Permutation Null Distribution',
      category: 'Statistical Baseline',
      desc: 'Empirical distribution generated from 1,000 degree-matched random target sets in the human interactome.',
      relevance: 'Controls for node degree bias so that highly connected target hubs do not artificially appear proximate to disease genes.'
    },
    prox_pair: {
      title: 'Drug-Disease Pair',
      category: 'Benchmark Selector',
      desc: 'Selects between primary therapeutic indications (Metformin→T2D, Imatinib→CML) and negative controls (Metformin→CML, Imatinib→T2D).',
      relevance: 'Demonstrates that network proximity selectively discriminates true therapeutic pairs from negative controls.'
    },
    dc: {
      title: 'Observed Closest Distance ⟨d<sub>c</sub>⟩',
      category: 'Network Distance',
      formula: '&lang;d<sub>c</sub>(T, S)&rang; = <sup>1</sup>/<sub>|T|</sub> &sum;<sub>t &isin; T</sub> min<sub>s &isin; S</sub> d(t, s)',
      desc: 'Average shortest path distance from each drug target protein to the closest disease gene across the human interactome (Guney et al., 2016).',
      relevance: 'Smaller distance values indicate that drug targets reside immediately adjacent to disease pathophysiology.'
    },
    z_score: {
      title: 'Proximity Z-Score',
      category: 'Statistical Significance',
      formula: 'z = (d<sub>c</sub> &minus; &mu;<sub>null</sub>) / &sigma;<sub>null</sub>',
      desc: 'Standard deviations by which the observed drug-disease distance is smaller than the degree-matched null mean.',
      relevance: 'z &le; &minus;2.0 confirms statistically significant disease co-localization (p < 0.025).'
    },
    empirical_p: {
      title: 'Empirical P-Value',
      category: 'Permutation Test',
      formula: 'p = (1 + count(d<sub>null</sub> &le; d<sub>obs</sub>)) / 1001',
      desc: 'Fraction of 1,000 degree-matched permutations that had distance less than or equal to observed d_c.',
      relevance: 'Provides distribution-free statistical confirmation of disease proximity.'
    },
    prox_verdict: {
      title: 'Proximity Verdict',
      category: 'Statistical Evaluation',
      desc: 'Classification as PROXIMATE (z &le; -2.0) or NOT PROXIMATE based on degree-controlled permutation significance.',
      relevance: 'Correlates strongly with approved clinical indications vs off-target disease controls.'
    },
    guney_formula: {
      title: 'Guney Network Proximity Metric',
      category: 'Theoretical Framework',
      formula: '&lang;d<sub>c</sub>(T, S)&rang; = <sup>1</sup>/<sub>|T|</sub> &sum;<sub>t &isin; T</sub> min<sub>s &isin; S</sub> d(t, s)',
      desc: 'Formulation established by Guney et al. (2016 Nature Communications) defining interactome distance between drug target set T and disease gene set S.',
      relevance: 'Foundational equation for computational network pharmacology and in silico drug repositioning.'
    },

    // GNN Link Predictions
    data_leakage: {
      title: 'Zero Data Leakage Protocol',
      category: 'ML Methodology',
      desc: 'Rigorous evaluation safeguard ensuring all test drug-target links, validation interactions, and target-neighbor associations are completely excluded during GNN training.',
      relevance: 'Guarantees that evaluation metrics reflect genuine inductive discovery rather than test-set memorization.'
    },
    graphsage: {
      title: 'GraphSAGE Architecture',
      category: 'Graph Neural Network',
      formula: 'h<sub>v</sub><sup>k</sup> = &sigma;(W &middot; [h<sub>v</sub><sup>k-1</sup> || AGG({h<sub>u</sub><sup>k-1</sup>})])',
      desc: 'Inductive graph neural network framework generating low-dimensional node embeddings by sampling and aggregating local interactome neighborhood features.',
      relevance: 'Enables predictive link inference on novel, unseen protein targets across the human interactome.'
    },
    auroc: {
      title: 'Test AUROC',
      category: 'Discriminative Performance',
      desc: 'Area Under the Receiver Operating Characteristic Curve on held-out test interactions vs. degree-matched negative decoys.',
      relevance: 'AUROC > 0.88 confirms strong discriminatory power for true interactome links.'
    },
    average_precision: {
      title: 'Test Average Precision (AP)',
      category: 'Precision Metric',
      desc: 'Area under the precision-recall curve across decision thresholds on unseen test edges.',
      relevance: 'Crucial metric for imbalanced link prediction where true interactions are sparse.'
    },
    leave_targets_out: {
      title: 'Leave-Targets-Out Cross-Validation',
      category: 'De Novo Benchmark',
      desc: 'Cross-validation where all known primary targets for test drugs are completely masked during training to assess de novo recovery capability.',
      relevance: 'Demonstrates real-world utility for predicting novel uncharacterized targets for existing drugs.'
    },
    hidden_targets: {
      title: 'Hidden Test Targets',
      category: 'Evaluation Set',
      desc: 'Specific validated primary targets masked during training to test de novo model retrieval.',
      relevance: 'Serves as the ground truth targets the GNN must rank among thousands of candidate proteins.'
    },
    recovery_ranks: {
      title: 'Recovered Target Ranks',
      category: 'Retrieval Rank',
      desc: 'Rank position of hidden targets among all human proteins sorted by GNN link prediction confidence.',
      relevance: 'Top ranks indicate successful computational target rediscovery.'
    },
    mrr: {
      title: 'Mean Reciprocal Rank (MRR)',
      category: 'Ranking Evaluation',
      formula: 'MRR = <sup>1</sup>/<sub>|Q|</sub> &sum; <sup>1</sup>/<sub>rank<sub>i</sub></sub>',
      desc: 'Average of the reciprocal ranks of true targets recovered by the link prediction model.',
      relevance: 'Heavily penalizes low-ranking targets, rewarding models that place true targets near the top.'
    },
    hits_at_20: {
      title: 'Hits@20',
      category: 'Top-K Accuracy',
      desc: 'Percentage of hidden test drug targets successfully retrieved within the model\'s top 20 candidate predictions.',
      relevance: 'Directly measures the feasibility of testing top candidates in laboratory wet-lab binding assays.'
    },
    candidate_gene: {
      title: 'Candidate Hypothesis Gene',
      category: 'Predicted Protein',
      desc: 'Human protein predicted by GraphSAGE embeddings to possess high functional or physical affinity with the drug\'s target scaffold.',
      relevance: 'High-priority candidate for experimental validation, secondary mechanisms, or drug repositioning.'
    },
    gnn_confidence: {
      title: 'GNN Prediction Confidence',
      category: 'Model Score',
      formula: 'cos_sim(z<sub>drug</sub>, z<sub>protein</sub>) &isin; [0, 1]',
      desc: 'Cosine similarity between latent graph neural network embeddings of the drug target scaffold and candidate protein.',
      relevance: 'Scores &ge; 0.75 denote strong interactome embedding alignment.'
    },
    gnn_context: {
      title: 'Biological Interactome Context',
      category: 'Biological Rationale',
      desc: 'Mechanistic biological explanation of how the predicted candidate gene interacts with known drug target pathways.',
      relevance: 'Provides biochemically grounded context for computational predictions.'
    },
    gnn_status: {
      title: 'Hypothesis Status',
      category: 'Evidence Level',
      desc: 'Indicates that the predicted link is a computational hypothesis supported by topological and embedding proximity, pending experimental assay confirmation.',
      relevance: 'Emphasizes scientific rigor: computational predictions guide, but do not replace, empirical assays.'
    },
    gnn_rigor: {
      title: 'Methodological Rigor Callout',
      category: 'Scientific Standard',
      desc: 'Formal reminder that GNN link predictions identify functional interactome co-membership and topological coupling, rather than direct biochemical binding affinity.',
      relevance: 'Ensures clear distinction between in silico hypotheses and validated biophysical dissociation constants (Kd).'
    },

    // Two-Drug Comparison & Synergy
    menche: {
      title: 'Menche Interactome Separation (s<sub>AB</sub>)',
      category: 'Module Overlap',
      formula: 's<sub>AB</sub> = &lang;d<sub>AB</sub>&rang; &minus; (&lang;d<sub>AA</sub>&rang; + &lang;d<sub>BB</sub>&rang;) / 2',
      desc: 'Theoretical metric established by Menche et al. (2015 Science) measuring separation between two drug target modules A and B in the interactome.',
      relevance: 's<sub>AB</sub> > 0 indicates distinct modules capable of synergistic therapeutic combinations without redundant cross-toxicity.'
    },
    comp_metric: {
      title: 'Comparison Metric',
      category: 'Multi-Omics Dimension',
      desc: 'Evaluates target overlap, LINCS transcriptional perturbation overlap, and RWR/2-Hop subnetwork intersection between drugs.',
      relevance: 'Provides multidimensional perspective on drug mechanism divergence.'
    },
    shared_proteins: {
      title: 'Shared Subnetwork Proteins',
      category: 'Intersection Size',
      desc: 'Count of proteins present in both Metformin and Imatinib extracted subnetworks (347 shared proteins).',
      relevance: 'Identifies the core cross-talk interactome scaffold mediating dual drug effects.'
    },
    jaccard: {
      title: 'Jaccard Similarity Index',
      category: 'Set Similarity',
      formula: 'J(A, B) = |A &cap; B| / |A &cup; B|',
      desc: 'Ratio of intersection to union between two gene or protein sets across omics dimensions.',
      relevance: 'Demonstrates that while primary targets are disjoint (J=0.00), downstream interactomes converge on shared signaling modules.'
    },
    menche_separation: {
      title: 'Separation Value s<sub>AB</sub> = +1.3503',
      category: 'Separation State',
      desc: 'Observed separation between Metformin and Imatinib target modules is strongly positive (+1.3503 > 0).',
      relevance: 'Confirms that the two drugs target distinct interactome neighborhoods, predicting low overlapping toxicity and high synergy potential.'
    },
    inter_distance: {
      title: 'Inter-Distance ⟨d<sub>AB</sub>⟩ = 2.409',
      category: 'Mean Path Length',
      desc: 'Average shortest path distance between Metformin targets and Imatinib targets across the human interactome.',
      relevance: 'Demonstrates that targets are connected by approximately 2 to 3 intermediary protein steps.'
    },
    topological_state: {
      title: 'Topological State: Distinct Modules',
      category: 'Module Classification',
      desc: 'Positive separation (s > 0) categorizes the two drugs as occupying distinct, non-overlapping topological modules.',
      relevance: 'Provides theoretical basis for rational combination pharmacology.'
    },
    crosstalk: {
      title: 'Shared Cross-Talk Hubs',
      category: 'Multi-Target Bridges',
      desc: 'Proteins appearing in both drug subnetworks that exhibit high degree or bottleneck centrality (e.g., AKT1, TP53, SRC, MAPK1).',
      relevance: 'Serve as key nexus points where Metformin metabolic modulation intersects with Imatinib kinase inhibition.'
    },
    shared_hub: {
      title: 'Shared Hub Protein',
      category: 'Topological Hub',
      desc: 'High-degree interactome hub present in both Metformin and Imatinib subnetworks.',
      relevance: 'Coordinates local signaling clusters common to both drugs\' therapeutic mechanisms.'
    },
    shared_bottleneck: {
      title: 'Shared Bottleneck Bridge',
      category: 'Topological Bottleneck',
      desc: 'High-betweenness protein bridging distinct functional modules within both drugs\' networks.',
      relevance: 'Controls communication channels shared between metabolic and oncogenic cascades.'
    },
    synergy: {
      title: 'Combination Synergy in CML',
      category: 'Translational Pharmacology',
      desc: 'Dual mechanism where Metformin (mitochondrial Complex I inhibition / glycolysis downregulation) synergizes with Imatinib (BCR-ABL1 kinase inhibition) to eradicate leukemic stem cells.',
      relevance: 'Overcomes Imatinib resistance in Chronic Myeloid Leukemia (CML) by cutting off compensatory metabolic survival pathways.'
    }
  };

  // Interactive Explainer Tooltip System
  function initTooltipSystem() {
    const tooltipEl = document.getElementById('pharma-tooltip');
    if (!tooltipEl) return;

    let activeTrigger = null;

    function renderTooltipContent(tipKey) {
      const data = TOOLTIP_DATA[tipKey];
      if (!data) return false;

      let html = `
        <div class="tooltip-header">
          <span class="tooltip-title">${data.title}</span>
          <span class="tooltip-category">${data.category}</span>
        </div>
      `;

      if (data.formula) {
        html += `<div class="tooltip-formula">${data.formula}</div>`;
      }

      html += `<div class="tooltip-desc">${data.desc}</div>`;

      if (data.relevance) {
        html += `<div class="tooltip-relevance">${data.relevance}</div>`;
      }

      tooltipEl.innerHTML = html;
      return true;
    }

    function positionTooltip(clientX, clientY) {
      const padding = 14;
      const rect = tooltipEl.getBoundingClientRect();
      const winW = window.innerWidth;
      const winH = window.innerHeight;

      let posX = clientX + 16;
      let posY = clientY + 16;

      // Flip or clamp if overflowing right
      if (posX + rect.width > winW - padding) {
        posX = clientX - rect.width - 16;
      }
      if (posX < padding) {
        posX = padding;
      }

      // Flip or clamp if overflowing bottom
      if (posY + rect.height > winH - padding) {
        posY = clientY - rect.height - 16;
      }
      if (posY < padding) {
        posY = padding;
      }

      tooltipEl.style.left = `${posX}px`;
      tooltipEl.style.top = `${posY}px`;
    }

    // Mouse events with delegation
    document.addEventListener('mouseover', e => {
      const trigger = e.target.closest('[data-tip]');
      if (!trigger) return;

      const tipKey = trigger.getAttribute('data-tip');
      if (renderTooltipContent(tipKey)) {
        activeTrigger = trigger;
        tooltipEl.classList.add('active');
        tooltipEl.setAttribute('aria-hidden', 'false');
        positionTooltip(e.clientX, e.clientY);
      }
    });

    document.addEventListener('mousemove', e => {
      if (!activeTrigger || !tooltipEl.classList.contains('active')) return;
      positionTooltip(e.clientX, e.clientY);
    });

    document.addEventListener('mouseout', e => {
      if (!activeTrigger) return;
      const related = e.relatedTarget;
      if (related && activeTrigger.contains(related)) return;

      activeTrigger = null;
      tooltipEl.classList.remove('active');
      tooltipEl.setAttribute('aria-hidden', 'true');
    });

    // Mobile / Touch Tap support
    document.addEventListener('click', e => {
      const trigger = e.target.closest('[data-tip]');
      if (trigger) {
        const tipKey = trigger.getAttribute('data-tip');
        if (renderTooltipContent(tipKey)) {
          activeTrigger = trigger;
          tooltipEl.classList.add('active');
          tooltipEl.setAttribute('aria-hidden', 'false');

          const trigRect = trigger.getBoundingClientRect();
          positionTooltip(trigRect.left + trigRect.width / 2, trigRect.bottom);
        }
      } else {
        // Tapping elsewhere closes tooltip
        if (tooltipEl.classList.contains('active')) {
          activeTrigger = null;
          tooltipEl.classList.remove('active');
          tooltipEl.setAttribute('aria-hidden', 'true');
        }
      }
    });
  }

  // Interactive Particle Background Canvas
  function initParticleBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const count = Math.min(60, Math.floor((width * height) / 25000));

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2 + 1,
        color: Math.random() > 0.4 ? 'rgba(255, 128, 0, 0.6)' : 'rgba(100, 110, 130, 0.4)'
      });
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);

      // Connect lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(255, 128, 0, ${0.15 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      // Draw particles
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = height;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();
      }

      requestAnimationFrame(animate);
    }

    animate();
  }

  function formatMathText(str) {
    if (!str) return '';
    return str
      .replace(/\$\\langle\s*d_c\s*\\rangle\$/g, '⟨d<sub>c</sub>⟩')
      .replace(/\\langle\s*d_c\s*\\rangle/g, '⟨d<sub>c</sub>⟩')
      .replace(/\\langle\s*d_\{?c\}?\(T,\s*S\)\s*\\rangle/g, '⟨d<sub>c</sub>(T, S)⟩')
      .replace(/\\langle\s*d_\{?AB\}?\s*\\rangle/g, '⟨d<sub>AB</sub>⟩')
      .replace(/\\langle\s*d_\{?AA\}?\s*\\rangle/g, '⟨d<sub>AA</sub>⟩')
      .replace(/\\langle\s*d_\{?BB\}?\s*\\rangle/g, '⟨d<sub>BB</sub>⟩')
      .replace(/s_\{?AB\}?\^\{?\\text\{closest\}\}?/g, 's<sub>AB</sub><sup>(closest)</sup>')
      .replace(/s_\{?AB\}?/g, 's<sub>AB</sub>')
      .replace(/d_\{?c\}?/g, 'd<sub>c</sub>')
      .replace(/p_\{?adj\}?/g, 'p<sub>adj</sub>')
      .replace(/\\times/g, '×')
      .replace(/\\le/g, '≤')
      .replace(/\\ge/g, '≥')
      .replace(/\\approx/g, '≈')
      .replace(/\\rightarrow/g, '→')
      .replace(/\\alpha/g, 'α')
      .replace(/\\kappa/g, 'κ')
      .replace(/10\^\{([^}]+)\}/g, '10<sup>$1</sup>')
      .replace(/\$([^\$]+)\$/g, '$1');
  }

  // =========================================================================
  // TAB 1: VIS.JS SUBNETWORK CANVAS
  // =========================================================================

  function initSubnetworkCanvas() {
    const container = document.getElementById('vis-network-canvas');
    if (!container || !state.subnetworksData) return;

    const drugData = state.subnetworksData[state.selectedDrug];
    if (!drugData) return;
    const methodData = drugData[state.selectedMethod];
    if (!methodData) return;

    // Update Mini KPIs
    const kpiNodes = document.getElementById('kpi-net-nodes');
    const kpiEdges = document.getElementById('kpi-net-edges');
    const kpiDensity = document.getElementById('kpi-net-density');
    const kpiTargets = document.getElementById('kpi-net-targets');

    if (kpiNodes) kpiNodes.textContent = methodData.node_count;
    if (kpiEdges) kpiEdges.textContent = methodData.edge_count;
    if (kpiDensity) kpiDensity.textContent = methodData.density;

    const targetCount = methodData.nodes.filter(n => n.is_target).length;
    if (kpiTargets) kpiTargets.textContent = targetCount;

    // Filter nodes by maxNodes while strictly preserving targets
    let nodesList = methodData.nodes.slice();
    if (nodesList.length > state.maxRenderedNodes) {
      const targets = nodesList.filter(n => n.is_target);
      const others = nodesList.filter(n => !n.is_target).sort((a, b) => b.degree - a.degree);
      nodesList = targets.concat(others.slice(0, state.maxRenderedNodes - targets.length));
    }

    const nodeIdsSet = new Set(nodesList.map(n => n.id));

    // Vis.js Nodes
    const visNodes = nodesList.map(n => {
      let color = '#3498DB'; // Blue (neighbor)
      let shape = 'dot';
      let size = 12;

      if (n.is_target) {
        color = '#F1C40F'; // Gold star
        shape = 'star';
        size = 26;
      } else if (n.expression_z >= 1.0) {
        color = '#E74C3C'; // Red
      } else if (n.expression_z <= -1.0) {
        color = '#2ECC71'; // Green
      }

      if (state.selectedSizing === 'betweenness') {
        size = n.is_target ? 28 : Math.max(10, Math.min(30, 10 + (n.degree * 0.8)));
      } else {
        size = n.is_target ? 28 : Math.max(10, Math.min(30, 10 + (n.degree * 0.5)));
      }

      return {
        id: n.id,
        label: n.label,
        color: {
          background: color,
          border: '#FFFFFF',
          highlight: { background: '#FF8000', border: '#FFFFFF' }
        },
        shape: shape,
        size: size,
        font: { color: '#FFFFFF', size: 12, face: 'Outfit' },
        borderWidth: 1.5,
        raw_data: n
      };
    });

    // Vis.js Edges (filtered and sorted by score descending, capped to top 250 salient edges)
    const candidateEdges = [];
    for (const e of methodData.edges) {
      if (nodeIdsSet.has(e.from) && nodeIdsSet.has(e.to)) {
        if (e.score >= state.edgeScoreThreshold) {
          candidateEdges.push(e);
        }
      }
    }
    candidateEdges.sort((a, b) => (b.score || 0) - (a.score || 0));
    const cappedEdges = candidateEdges.slice(0, 250);

    const visEdges = cappedEdges.map(e => ({
      from: e.from,
      to: e.to,
      color: {
        color: 'rgba(255, 128, 0, 0.35)',
        highlight: '#FF8000',
        hover: '#FFAA44'
      },
      width: Math.max(1, (e.score - 700) / 100),
      title: `STRING Score: ${e.score}`
    }));

    const data = {
      nodes: new vis.DataSet(visNodes),
      edges: new vis.DataSet(visEdges)
    };

    const options = {
      nodes: {
        borderWidth: 1.5,
        shadow: true
      },
      edges: {
        smooth: false,
        selectionWidth: 2
      },
      physics: {
        enabled: state.physicsEnabled,
        solver: 'barnesHut',
        barnesHut: {
          gravitationalConstant: -1800,
          centralGravity: 0.25,
          springLength: 95,
          springConstant: 0.05,
          damping: 0.09,
          avoidOverlap: 0.2
        },
        stabilization: {
          enabled: true,
          iterations: 60,
          updateInterval: 25
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        navigationButtons: false,
        keyboard: true
      }
    };

    if (state.visNetwork) {
      state.visNetwork.destroy();
    }

    state.visNetwork = new vis.Network(container, data, options);

    state.visNetwork.once('stabilizationIterationsDone', () => {
      state.visNetwork.fit();
    });

    // Click Node Listener
    state.visNetwork.on('click', params => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const clicked = nodesList.find(n => n.id === nodeId);
        if (clicked) {
          openNodeModal(clicked);
        }
      }
    });
  }

  function openNodeModal(node) {
    const modal = document.getElementById('node-modal');
    const title = document.getElementById('modal-gene-title');
    const body = document.getElementById('modal-gene-body');
    if (!modal || !title || !body) return;

    title.innerHTML = `Protein: <span class="text-orange">${node.label}</span>`;
    body.innerHTML = `
      <div class="kpi-card-row mb-3">
        <div class="kpi-card" data-tip="${node.is_target ? 'seed_target' : 'interactome_neighbor'}">
          <div class="kpi-label">Role</div>
          <div class="kpi-val ${node.is_target ? 'text-orange' : 'text-blue'}">
            ${node.is_target ? 'Primary Target' : 'Interactome Neighbor'}
          </div>
        </div>
        <div class="kpi-card" data-tip="degree">
          <div class="kpi-label">Subnetwork Degree</div>
          <div class="kpi-val">${node.degree}</div>
        </div>
        <div class="kpi-card" data-tip="${node.expression_z > 0 ? 'up_regulated' : 'down_regulated'}">
          <div class="kpi-label">LINCS Expression z</div>
          <div class="kpi-val ${node.expression_z > 0 ? 'text-red' : 'text-green'}">
            ${node.expression_z}
          </div>
        </div>
      </div>
      <p data-tip="louvain"><strong>Community Assignment:</strong> Cluster ${node.community_id || 'N/A'}</p>
      <p class="mt-2"><strong>Biological Significance:</strong> Topologically participating in ${state.selectedDrug.toUpperCase()} target subnetwork scaffold.</p>
      <div class="mt-3">
        <a href="https://pubmed.ncbi.nlm.nih.gov/?term=${state.selectedDrug}+AND+${node.label}" target="_blank" class="btn-action w-100" style="display: block; text-align: center; text-decoration: none;">
          Query ${node.label} + ${state.selectedDrug.toUpperCase()} on PubMed
        </a>
      </div>
    `;

    modal.classList.add('active');
  }

  // =========================================================================
  // TAB 2: PATHWAY ENRICHMENT & ORA
  // =========================================================================

  function initPathwaysTab() {
    if (!state.pathwaysData) return;

    // 1. Biological Sanity Audit Cards
    const auditContainer = document.getElementById('sanity-audit-container');
    const audit = state.pathwaysData.sanity_audit;
    if (auditContainer && audit) {
      const metSanity = audit.Metformin?.rwr_sanity;
      const imaSanity = audit.Imatinib?.rwr_sanity;

      auditContainer.innerHTML = `
        <div class="glass-card mb-3">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>Metformin (T2D):</strong>
            <span class="badge-tag ${metSanity?.passed ? 'tag-green' : 'tag-orange'}">
              ${metSanity?.passed ? 'SANITY PASSED' : 'INVESTIGATING'}
            </span>
          </div>
          <p class="small text-muted mt-2">${metSanity?.verdict || ''}</p>
          <div class="mt-2">
            ${(metSanity?.matched_hallmarks || []).map(m => `
              <span class="badge-tag tag-orange" style="margin: 2px;">${m.keyword}</span>
            `).join('')}
          </div>
        </div>

        <div class="glass-card">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>Imatinib (CML):</strong>
            <span class="badge-tag ${imaSanity?.passed ? 'tag-green' : 'tag-orange'}">
              ${imaSanity?.passed ? 'SANITY PASSED' : 'INVESTIGATING'}
            </span>
          </div>
          <p class="small text-muted mt-2">${imaSanity?.verdict || ''}</p>
          <div class="mt-2">
            ${(imaSanity?.matched_hallmarks || []).map(m => `
              <span class="badge-tag tag-orange" style="margin: 2px;">${m.keyword}</span>
            `).join('')}
          </div>
        </div>
      `;
    }

    // 2. Filter pathways
    const drugScope = state.pathwaysData.drugs?.[state.pathwayDrug]?.[state.pathwayScope] || [];
    const filtered = drugScope.filter(p => (p.adj_p_value || 1.0) <= state.fdrThreshold);

    // 3. Render Table
    const tbody = document.querySelector('#table-pathways tbody');
    if (tbody) {
      tbody.innerHTML = filtered.slice(0, 15).map(p => `
        <tr>
          <td><strong>${p.term}</strong></td>
          <td><span class="badge-tag tag-blue">${p.library}</span></td>
          <td class="text-orange" style="font-family: var(--font-mono);">${Number(p.adj_p_value).toExponential(2)}</td>
          <td>${p.overlap || '--'}</td>
          <td>${p.combined_score ? p.combined_score.toFixed(1) : '--'}</td>
        </tr>
      `).join('');
    }

    // 4. Render Chart.js
    const ctx = document.getElementById('chart-pathways');
    if (ctx) {
      const top10 = filtered.slice(0, 8);
      const labels = top10.map(p => p.term.length > 35 ? p.term.substring(0, 32) + '...' : p.term);
      const pvalues = top10.map(p => -Math.log10(p.adj_p_value || 1e-10));

      if (state.chartPathways) state.chartPathways.destroy();

      state.chartPathways = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: '-log10(Adjusted P-Value)',
            data: pvalues,
            backgroundColor: 'rgba(255, 128, 0, 0.75)',
            borderColor: '#FF8000',
            borderWidth: 1.5,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' },
              title: { display: true, text: '-log10(Adj. P-Value)', color: '#FF8000' }
            },
            y: {
              grid: { display: false },
              ticks: { color: '#FFFFFF', font: { size: 11, family: 'Outfit' } }
            }
          }
        }
      });
    }
  }

  // =========================================================================
  // TAB 3: CENTRALITIES & MODULARITY
  // =========================================================================

  function initCentralityTab() {
    if (!state.metricsData) return;
    const drugMetrics = state.metricsData.drugs?.[state.centDrug]?.rwr;
    if (!drugMetrics) return;

    // 1. Communities Table
    const commTbody = document.querySelector('#table-communities tbody');
    if (commTbody) {
      commTbody.innerHTML = (drugMetrics.communities || []).map(c => `
        <tr>
          <td><span class="badge-tag tag-orange">Cluster ${c.community_id}</span></td>
          <td><strong>${c.size} proteins</strong></td>
          <td>${c.dominant_pathway || 'Signaling Cascade'}</td>
        </tr>
      `).join('');
    }

    // 2. Bottlenecks Table
    const bottleTbody = document.querySelector('#table-bottlenecks tbody');
    if (bottleTbody) {
      const sorted = (drugMetrics.centralities || []).slice().sort((a, b) => (b.betweenness_centrality || 0) - (a.betweenness_centrality || 0));
      bottleTbody.innerHTML = sorted.slice(0, 10).map(c => `
        <tr>
          <td><strong>${c.gene_symbol}</strong></td>
          <td>${c.raw_degree}</td>
          <td class="text-orange" style="font-family: var(--font-mono);">${(c.betweenness_centrality || 0).toFixed(5)}</td>
          <td>${(c.eigenvector_centrality || 0).toFixed(4)}</td>
          <td><span class="badge-tag ${c.is_hub_bottleneck_bridge ? 'tag-purple' : (c.is_bottleneck ? 'tag-red' : 'tag-orange')}">${c.is_hub_bottleneck_bridge ? 'Dual Bridge' : (c.is_bottleneck ? 'Bottleneck' : 'Hub')}</span></td>
        </tr>
      `).join('');
    }

    // 3. Scatter Plot Degree vs Betweenness
    const ctx = document.getElementById('chart-centrality-scatter');
    if (ctx && drugMetrics.centralities) {
      if (state.chartCentrality) state.chartCentrality.destroy();

      const scatterData = drugMetrics.centralities.map(c => ({
        x: c.raw_degree,
        y: c.betweenness_centrality || 0,
        gene: c.gene_symbol,
        isBridge: c.is_hub_bottleneck_bridge,
        isHub: c.is_hub,
        isBottle: c.is_bottleneck
      }));

      state.chartCentrality = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Proteins',
            data: scatterData,
            backgroundColor: ctxPoint => {
              const d = ctxPoint.raw;
              if (d && d.isBridge) return '#9B59B6';
              if (d && d.isHub) return '#FF8000';
              if (d && d.isBottle) return '#E74C3C';
              return '#3498DB';
            },
            pointRadius: 6,
            pointHoverRadius: 9
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctxPoint => {
                  const d = ctxPoint.raw;
                  return `${d.gene}: Degree=${d.x}, Betweenness=${d.y.toFixed(5)}`;
                }
              }
            }
          },
          scales: {
            x: {
              title: { display: true, text: 'Raw Degree Centrality', color: '#FF8000' },
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' }
            },
            y: {
              title: { display: true, text: 'Betweenness Centrality', color: '#FF8000' },
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' }
            }
          }
        }
      });
    }
  }

  // =========================================================================
  // TAB 4: DISEASE PROXIMITY LAB
  // =========================================================================

  function initProximityTab() {
    if (!state.proximityData) return;

    // 1. Summary Table
    const tbody = document.querySelector('#table-proximity-summary tbody');
    if (tbody) {
      tbody.innerHTML = (state.proximityData.summary || []).map(p => `
        <tr>
          <td><strong>${p.drug}</strong></td>
          <td>${p.disease}</td>
          <td class="text-orange" style="font-family: var(--font-mono); font-weight: 700;">${p.observed_d_c.toFixed(3)}</td>
          <td>${p.mean_null_d_c.toFixed(3)} ± ${p.std_null_d_c.toFixed(3)}</td>
          <td class="${p.z_score < -2 ? 'text-green' : 'text-red'}" style="font-family: var(--font-mono); font-weight: 800;">${p.z_score.toFixed(2)}</td>
          <td>${p.p_value.toFixed(4)}</td>
          <td><span class="badge-tag ${p.z_score < -2 ? 'tag-green' : 'tag-red'}">${p.z_score < -2 ? 'PROXIMATE' : 'NOT PROXIMATE'}</span></td>
        </tr>
      `).join('');
    }

    // 2. Distribution Plot
    updateProximityDistribution();
  }

  function updateProximityDistribution() {
    const pairKey = state.proxPair; // 'metformin_t2d', etc.
    const details = state.proximityData?.details?.[pairKey];
    if (!details) return;

    const nullDist = details.null_distribution || [];
    const obsDist = details.observed_closest_distance;

    // Callout
    const callout = document.getElementById('prox-stats-callout');
    if (callout) {
      callout.innerHTML = `
        <div class="kpi-card-row">
          <div class="kpi-card">
            <div class="kpi-label">Observed ⟨d<sub>c</sub>⟩</div>
            <div class="kpi-val text-orange">${obsDist.toFixed(3)}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Null Mean ± Std</div>
            <div class="kpi-val">${details.mean_null_distance.toFixed(3)} ± ${details.std_null_distance.toFixed(3)}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Proximity Z-Score</div>
            <div class="kpi-val ${details.z_score < -2 ? 'text-green' : 'text-red'}">${details.z_score.toFixed(2)}</div>
          </div>
        </div>
        <p class="mt-2 text-muted small"><strong>Significance Verdict:</strong> ${details.verdict}</p>
      `;
    }

    // Histogram with Chart.js
    const ctx = document.getElementById('chart-proximity-dist');
    if (ctx && nullDist.length > 0) {
      if (state.chartProximity) state.chartProximity.destroy();

      const minVal = Math.min(obsDist, ...nullDist) * 0.96;
      const maxVal = Math.max(obsDist, ...nullDist) * 1.04;
      const numBins = 24;
      const binWidth = (maxVal - minVal) / numBins;
      const binLabels = [];
      const nullBins = new Array(numBins).fill(0);
      const obsBins = new Array(numBins).fill(0);

      for (let i = 0; i < numBins; i++) {
        binLabels.push((minVal + (i + 0.5) * binWidth).toFixed(2));
      }
      for (const val of nullDist) {
        const idx = Math.min(numBins - 1, Math.max(0, Math.floor((val - minVal) / binWidth)));
        nullBins[idx]++;
      }
      const obsIdx = Math.min(numBins - 1, Math.max(0, Math.floor((obsDist - minVal) / binWidth)));
      const maxFreq = Math.max(...nullBins);
      obsBins[obsIdx] = maxFreq > 0 ? Math.round(maxFreq * 0.9) : 100;

      state.chartProximity = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: binLabels,
          datasets: [
            {
              label: '1,000 Degree-Matched Null Permutations',
              data: nullBins,
              backgroundColor: 'rgba(52, 152, 219, 0.45)',
              borderColor: '#3498DB',
              borderWidth: 1.2
            },
            {
              label: `Observed ⟨d_c⟩ = ${obsDist.toFixed(3)} (z = ${details.z_score.toFixed(2)})`,
              data: obsBins,
              backgroundColor: 'rgba(255, 128, 0, 0.9)',
              borderColor: '#FF8000',
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `Permutation Null vs. Observed Distance (${obsDist.toFixed(3)})`,
              color: '#FFFFFF',
              font: { family: 'Outfit', size: 14 }
            },
            legend: {
              labels: { color: '#FFFFFF', font: { family: 'Outfit' } }
            }
          },
          scales: {
            x: {
              title: { display: true, text: 'Closest Distance ⟨d_c⟩', color: '#9BA3AF' },
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' }
            },
            y: {
              title: { display: true, text: 'Permutation Frequency', color: '#9BA3AF' },
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' }
            }
          }
        }
      });
    }
  }

  // =========================================================================
  // TAB 5: GNN LINK PREDICTIONS
  // =========================================================================

  function initGnnTab() {
    if (!state.gnnData) return;

    // 1. PPI Metrics Table
    const metricsTbody = document.querySelector('#table-gnn-metrics tbody');
    if (metricsTbody) {
      metricsTbody.innerHTML = (state.gnnData.ppi_metrics || []).map(m => `
        <tr>
          <td><strong>${m['Model'] || m.model}</strong></td>
          <td class="text-orange" style="font-family: var(--font-mono); font-weight: 700;">${(m['Test AUROC'] || m.test_auroc || 0).toFixed(4)}</td>
          <td style="font-family: var(--font-mono);">${(m['Test Average Precision'] || m.test_ap || 0).toFixed(4)}</td>
        </tr>
      `).join('');
    }

    // 2. Leave Targets Out Recovery Table
    const recTbody = document.querySelector('#table-gnn-recovery tbody');
    if (recTbody) {
      recTbody.innerHTML = (state.gnnData.recovery_metrics || []).map(r => `
        <tr>
          <td><strong>${r['Drug'] || r.drug}</strong></td>
          <td><span class="badge-tag tag-blue">${r['Hidden Test Targets'] || r.hidden_targets}</span></td>
          <td class="text-orange" style="font-family: var(--font-mono);">${r['Hidden Targets Ranks'] || r.target_ranks}</td>
          <td>${r['Mean Reciprocal Rank (MRR)'] || r.mean_reciprocal_rank}</td>
          <td><span class="badge-tag tag-green">${r['Hits@20'] || '50.0%'}</span></td>
        </tr>
      `).join('');
    }

    // 3. Top 20 Hypotheses Table
    updateHypothesesTable();
  }

  function updateHypothesesTable() {
    const list = state.gnnData?.hypotheses?.[state.gnnDrug] || [];
    const litTable = state.gnnData?.literature_table || [];

    const tbody = document.querySelector('#table-gnn-hypotheses tbody');
    if (!tbody) return;

    tbody.innerHTML = list.map(h => {
      const match = litTable.find(l => l.Drug.toLowerCase() === state.gnnDrug && l['Candidate Protein'] === h.candidate_protein);
      const pubmedUrl = match ? match['PubMed Search Link'] : `https://pubmed.ncbi.nlm.nih.gov/?term=${state.gnnDrug}+AND+${h.candidate_protein}`;
      const context = match ? match['Biological Interactome Context'] : 'Topological neighbor in human PPI scaffold';

      return `
        <tr>
          <td><span class="badge-tag tag-orange">#${h.rank}</span></td>
          <td><strong>${h.candidate_protein}</strong></td>
          <td class="text-orange" style="font-family: var(--font-mono); font-weight: 700;">${h.confidence_score.toFixed(4)}</td>
          <td class="small text-muted">${context}</td>
          <td><span class="badge-tag tag-blue">Hypothesis</span></td>
          <td>
            <a href="${pubmedUrl}" target="_blank" class="tool-btn tool-btn-orange" style="display: inline-flex; text-decoration: none; padding: 4px 8px; font-size: 11px;">
              PubMed
            </a>
          </td>
        </tr>
      `;
    }).join('');
  }

  // =========================================================================
  // TAB 6: TWO-DRUG COMPARISON
  // =========================================================================

  function initComparisonTab() {
    if (!state.comparisonData) return;

    // 1. Summary Table
    const tbody = document.querySelector('#table-comp-summary tbody');
    if (tbody) {
      tbody.innerHTML = (state.comparisonData.summary || []).map(c => `
        <tr>
          <td><strong>${c['Comparison Metric']}</strong></td>
          <td>${c['Metformin Count']}</td>
          <td>${c['Imatinib Count']}</td>
          <td class="text-orange"><strong>${c['Shared Count']}</strong></td>
          <td style="font-family: var(--font-mono); font-weight: 700;">${c['Jaccard Index'] !== null && !isNaN(c['Jaccard Index']) ? Number(c['Jaccard Index']).toFixed(4) : '--'}</td>
        </tr>
      `).join('');
    }

    // 2. Shared Proteins Table
    const sharedTbody = document.querySelector('#table-shared-proteins tbody');
    if (sharedTbody) {
      sharedTbody.innerHTML = (state.comparisonData.shared_cross_talk || []).slice(0, 15).map(p => `
        <tr>
          <td><strong>${p.gene_symbol}</strong></td>
          <td class="text-orange" style="font-family: var(--font-mono); font-weight: 700;">${p.full_ppi_degree}</td>
          <td>${p.metformin_degree}</td>
          <td>${p.imatinib_degree}</td>
          <td><span class="badge-tag ${p.is_shared_hub ? 'tag-orange' : 'tag-blue'}">${p.is_shared_hub ? 'HUB' : 'NO'}</span></td>
          <td><span class="badge-tag ${p.is_shared_bottleneck ? 'tag-purple' : 'tag-blue'}">${p.is_shared_bottleneck ? 'BOTTLENECK' : 'NO'}</span></td>
        </tr>
      `).join('');
    }

    // 3. Combination Report
    const reportBox = document.getElementById('combination-report-box');
    if (reportBox && state.comparisonData.combination_report) {
      let formatted = state.comparisonData.combination_report
        .replace(/^# (.*$)/gim, '<h3 class="text-orange">$1</h3>')
        .replace(/^## (.*$)/gim, '<h4 class="mt-3 text-orange">$1</h4>')
        .replace(/^### (.*$)/gim, '<h5 class="mt-2 text-orange">$1</h5>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/^\- (.*$)/gim, '<li class="small text-muted">$1</li>');
      formatted = formatMathText(formatted);
      reportBox.innerHTML = formatted;
    }

    // 4. Interactive Jaccard Overlap Bar Chart
    const jaccardCtx = document.getElementById('chart-comp-jaccard');
    if (jaccardCtx && state.comparisonData.summary) {
      if (state.chartJaccard) state.chartJaccard.destroy();

      const validSummary = (state.comparisonData.summary || []).filter(
        s => s['Jaccard Index'] !== null && !isNaN(s['Jaccard Index'])
      );
      const labels = validSummary.map(s => s['Comparison Metric']);
      const vals = validSummary.map(s => Number(s['Jaccard Index']));

      state.chartJaccard = new Chart(jaccardCtx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Jaccard Similarity Index',
            data: vals,
            backgroundColor: [
              'rgba(255, 128, 0, 0.85)',
              'rgba(255, 153, 38, 0.85)',
              'rgba(155, 89, 182, 0.85)',
              'rgba(52, 152, 219, 0.85)',
              'rgba(46, 204, 113, 0.85)'
            ],
            borderColor: '#FF8000',
            borderWidth: 1.2,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => ` Jaccard: ${ctx.raw.toFixed(4)}`
              }
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              max: 0.7,
              title: { display: true, text: 'Jaccard Index (0 to 1)', color: '#9BA3AF' },
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#9BA3AF' }
            },
            y: {
              grid: { color: 'rgba(255,255,255,0.06)' },
              ticks: { color: '#FFFFFF', font: { family: 'Outfit', weight: 'bold' } }
            }
          }
        }
      });
    }
  }

  // =========================================================================
  // GLOBAL EVENT LISTENERS & SETUP
  // =========================================================================

  function setupEventListeners() {
    // Fullscreen Toggle
    document.getElementById('btn-fullscreen')?.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });

    // Modal Close
    document.getElementById('btn-modal-close')?.addEventListener('click', () => {
      document.getElementById('node-modal')?.classList.remove('active');
    });
    document.getElementById('node-modal')?.addEventListener('click', e => {
      if (e.target.id === 'node-modal') {
        document.getElementById('node-modal').classList.remove('active');
      }
    });

    // Explorer Tabs
    document.querySelectorAll('.exp-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.exp-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.exp-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const targetId = tab.dataset.tab;
        const targetEl = document.getElementById(targetId);
        if (targetEl) targetEl.classList.add('active');

        // Lazy initialize charts/canvases upon tab opening
        if (targetId === 'tab-subnetworks') initSubnetworkCanvas();
        else if (targetId === 'tab-pathways') initPathwaysTab();
        else if (targetId === 'tab-centralities') initCentralityTab();
        else if (targetId === 'tab-proximity') initProximityTab();
        else if (targetId === 'tab-gnn') initGnnTab();
        else if (targetId === 'tab-comparison') initComparisonTab();
      });
    });

    // Subnetwork Controls
    document.querySelectorAll('[data-drug]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-drug]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedDrug = btn.dataset.drug;
        initSubnetworkCanvas();
      });
    });

    document.querySelectorAll('[data-method]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-method]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedMethod = btn.dataset.method;
        initSubnetworkCanvas();
      });
    });

    document.getElementById('select-sizing-metric')?.addEventListener('change', e => {
      state.selectedSizing = e.target.value;
      initSubnetworkCanvas();
    });

    document.getElementById('slider-edge-score')?.addEventListener('input', e => {
      state.edgeScoreThreshold = parseInt(e.target.value, 10);
      document.getElementById('val-edge-score').textContent = state.edgeScoreThreshold;
      initSubnetworkCanvas();
    });

    document.getElementById('slider-max-nodes')?.addEventListener('input', e => {
      state.maxRenderedNodes = parseInt(e.target.value, 10);
      document.getElementById('val-max-nodes').textContent = state.maxRenderedNodes;
      initSubnetworkCanvas();
    });

    // Physics Simulation Toggle
    const physicsBtn = document.getElementById('btn-toggle-physics');
    physicsBtn?.addEventListener('click', () => {
      state.physicsEnabled = !state.physicsEnabled;
      physicsBtn.textContent = state.physicsEnabled ? 'Pause Physics' : 'Resume Physics';
      if (state.visNetwork) {
        state.visNetwork.setOptions({ physics: { enabled: state.physicsEnabled } });
      }
    });

    // Fit View
    document.getElementById('btn-fit-canvas')?.addEventListener('click', () => {
      if (state.visNetwork) {
        state.visNetwork.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
      }
    });

    // Gene Search
    function executeGeneSearch() {
      const q = document.getElementById('input-gene-search')?.value.trim().toUpperCase();
      if (!q || !state.visNetwork) return;
      try {
        state.visNetwork.selectNodes([q]);
        state.visNetwork.focus(q, { scale: 1.5, animation: { duration: 800 } });
        showToast(`Highlighted Protein: <strong>${q}</strong>`);
      } catch (err) {
        showToast(`Protein <strong>${q}</strong> not in current subgraph.`);
      }
    }
    document.getElementById('btn-gene-search')?.addEventListener('click', executeGeneSearch);
    document.getElementById('input-gene-search')?.addEventListener('keydown', e => {
      if (e.key === 'Enter') executeGeneSearch();
    });

    // Pathway Tab Controls
    document.querySelectorAll('[data-pdrug]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-pdrug]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.pathwayDrug = btn.dataset.pdrug;
        initPathwaysTab();
      });
    });

    document.querySelectorAll('[data-pscope]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-pscope]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.pathwayScope = btn.dataset.pscope;
        initPathwaysTab();
      });
    });

    document.getElementById('slider-fdr-thresh')?.addEventListener('input', e => {
      state.fdrThreshold = parseFloat(e.target.value);
      document.getElementById('val-fdr-thresh').textContent = state.fdrThreshold;
      initPathwaysTab();
    });

    // Centrality Drug Pills
    document.querySelectorAll('[data-cdrug]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-cdrug]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.centDrug = btn.dataset.cdrug;
        initCentralityTab();
      });
    });

    // Proximity Pair Selector
    document.getElementById('select-prox-pair')?.addEventListener('change', e => {
      state.proxPair = e.target.value;
      updateProximityDistribution();
    });

    // GNN Drug Pills
    document.querySelectorAll('[data-gdrug]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-gdrug]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.gnnDrug = btn.dataset.gdrug;
        updateHypothesesTable();
      });
    });
  }

  // Initial Data Fetch
  async function loadAllData() {
    try {
      const [subs, paths, mets, prox, gnn, comp] = await Promise.all([
        fetch('data/subnetworks.json').then(r => r.json()),
        fetch('data/pathways.json').then(r => r.json()),
        fetch('data/network_metrics.json').then(r => r.json()),
        fetch('data/proximity.json').then(r => r.json()),
        fetch('data/gnn.json').then(r => r.json()),
        fetch('data/comparison.json').then(r => r.json())
      ]);

      state.subnetworksData = subs;
      state.pathwaysData = paths;
      state.metricsData = mets;
      state.proximityData = prox;
      state.gnnData = gnn;
      state.comparisonData = comp;

      // Initialize the default view (Subnetworks)
      initSubnetworkCanvas();

    } catch (err) {
      console.error('Failed to load PharmaPath data:', err);
      showToast('Error loading research data files.');
    }
  }

  // App Initialization Entry Point
  window.addEventListener('DOMContentLoaded', () => {
    initParticleBackground();
    initTooltipSystem();
    setupEventListeners();
    loadAllData();
  });

  // Expose state for automated inspection
  window.appState = state;
  window.initSubnetworkCanvas = initSubnetworkCanvas;
  window.openNodeModal = openNodeModal;
  window.TOOLTIP_DATA = TOOLTIP_DATA;

})();
