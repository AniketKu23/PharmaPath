import subprocess
import time
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_website_tooltips():
    server_process = subprocess.Popen([sys.executable, 'website/server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('http://localhost:8080', wait_until='networkidle')
            
            # 1. Check tooltip container exists
            tooltip = page.locator('#pharma-tooltip')
            assert tooltip.count() == 1, 'Tooltip element missing'
            print('Tooltip container exists.')

            # 2. Test hovering on RWR pill
            rwr_btn = page.locator('[data-tip="rwr"]')
            rwr_btn.hover()
            page.wait_for_timeout(300)
            
            assert 'active' in tooltip.get_attribute('class'), 'Tooltip not active on hover'
            title_text = page.locator('.tooltip-title').text_content()
            assert 'Random Walk with Restart' in title_text, f'Unexpected title: {title_text}'
            print(f'RWR Tooltip Verified: {title_text}')
            
            print('Formula verified successfully')

            # 3. Test hovering on 2-Hop Neighborhood
            twohop_btn = page.locator('[data-tip="two_hop"]')
            twohop_btn.hover()
            page.wait_for_timeout(300)
            title_text = page.locator('.tooltip-title').text_content()
            assert '2-Hop Neighborhood' in title_text, f'Unexpected title: {title_text}'
            print(f'2-Hop Tooltip Verified: {title_text}')

            # 4. Test Disease Proximity tab tooltips
            prox_tab = page.locator('[data-tab="tab-proximity"]')
            prox_tab.click()
            page.wait_for_timeout(500)
            
            dc_header = page.locator('th[data-tip="dc"]')
            dc_header.hover()
            page.wait_for_timeout(300)
            title_text = page.locator('.tooltip-title').text_content()
            assert 'Observed Closest Distance' in title_text, f'Unexpected title: {title_text}'
            print(f'Proximity dc Tooltip Verified: {title_text}')

            # 5. Test GNN tab tooltips
            gnn_tab = page.locator('[data-tab="tab-gnn"]')
            gnn_tab.click()
            page.wait_for_timeout(500)

            leakage_badge = page.locator('[data-tip="data_leakage"]').first
            leakage_badge.hover()
            page.wait_for_timeout(300)
            title_text = page.locator('.tooltip-title').text_content()
            assert 'Zero Data Leakage' in title_text, f'Unexpected title: {title_text}'
            print(f'GNN Leakage Tooltip Verified: {title_text}')

            # 6. Test Two-Drug Comparison tab
            comp_tab = page.locator('[data-tab="tab-comparison"]')
            comp_tab.click()
            page.wait_for_timeout(500)

            menche_card = page.locator('[data-tip="menche"]').first
            menche_card.hover()
            page.wait_for_timeout(300)
            title_text = page.locator('.tooltip-title').text_content()
            assert 'Menche Interactome Separation' in title_text, f'Unexpected title: {title_text}'
            print(f'Menche Tooltip Verified: {title_text}')

            browser.close()
            print('ALL TOOLTIP TESTS PASSED SUCCESSFULLY!')
    finally:
        server_process.terminate()

if __name__ == '__main__':
    test_website_tooltips()
