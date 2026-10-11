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
        <div class="kpi-card">
          <div class="kpi-label">Role</div>
          <div class="kpi-val ${node.is_target ? 'text-orange' : 'text-blue'}">
            ${node.is_target ? 'Primary Target' : 'Interactome Neighbor'}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Subnetwork Degree</div>
          <div class="kpi-val">${node.degree}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">LINCS Expression z</div>
          <div class="kpi-val ${node.expression_z > 0 ? 'text-red' : 'text-green'}">
            ${node.expression_z}
          </div>
        </div>
      </div>
      <p><strong>Community Assignment:</strong> Cluster ${node.community_id || 'N/A'}</p>
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
    setupEventListeners();
    loadAllData();
  });

  // Expose state for automated inspection
  window.appState = state;
  window.initSubnetworkCanvas = initSubnetworkCanvas;
  window.openNodeModal = openNodeModal;

})();
