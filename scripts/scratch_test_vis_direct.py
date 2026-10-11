from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 950})
    page.goto('http://localhost:8080')
    page.wait_for_timeout(1000)

    # Let's test inside floating-vis-test with 50 real nodes from methodData!
    res = page.evaluate("""() => {
        const testDiv = document.createElement('div');
        testDiv.id = 'floating-vis-test-2';
        testDiv.style.position = 'fixed';
        testDiv.style.top = '100px';
        testDiv.style.left = '100px';
        testDiv.style.width = '800px';
        testDiv.style.height = '500px';
        testDiv.style.background = '#0E1017';
        testDiv.style.zIndex = '99999';
        testDiv.style.border = '2px solid #FF8000';
        document.body.appendChild(testDiv);
        
        const state = window.appState;
        const d = state.subnetworksData.metformin.rwr;
        const nodes = d.nodes.slice(0, 50).map(n => ({
            id: n.id,
            label: n.label,
            color: n.is_target ? '#FF8000' : '#3498DB',
            size: n.is_target ? 24 : 14,
            shape: n.is_target ? 'star' : 'dot',
            font: { color: '#FFFFFF', size: 12 }
        }));
        const nodeIds = new Set(nodes.map(n => n.id));
        const edges = d.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to) && e.score >= 850).slice(0, 80).map(e => ({
            from: e.from,
            to: e.to,
            color: 'rgba(255, 128, 0, 0.5)',
            width: 1.5
        }));
        
        const net = new vis.Network(testDiv, {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges)
        }, {
            physics: {
                solver: 'barnesHut',
                barnesHut: {
                    gravitationalConstant: -1500,
                    centralGravity: 0.2,
                    springLength: 90,
                    springConstant: 0.05,
                    damping: 0.09
                },
                stabilization: { iterations: 40 }
            }
        });
        
        net.once('stabilizationIterationsDone', () => {
            net.fit();
        });
        
        return {
            nodesCount: nodes.length,
            edgesCount: edges.length
        };
    }""")
    print("Test 50 nodes with barnesHut:", res)
    page.wait_for_timeout(1500)
    page.screenshot(path="reports/screenshots/scratch_50_nodes_barneshut.png")
    b.close()
