from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto('http://localhost:8080')
    info = page.evaluate("""() => {
        return {
            hasVis: typeof vis !== 'undefined',
            visKeys: typeof vis !== 'undefined' ? Object.keys(vis) : [],
            hasDataSet: typeof vis !== 'undefined' && typeof vis.DataSet !== 'undefined',
            hasNetwork: typeof vis !== 'undefined' && typeof vis.Network !== 'undefined',
        };
    }""")
    print("Vis inspection:", info)
    b.close()
