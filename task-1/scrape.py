import asyncio
import random
import sqlite3
from playwright.async_api import async_playwright
from playwright_stealth import Stealth 

def setup_database():
    conn = sqlite3.connect('ecomm_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            name TEXT,
            price TEXT
        )
    ''')
    conn.commit()
    return conn

async def run_scraper():
    db_conn = setup_database()
    db_cursor = db_conn.cursor()

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("Navigating to the main Japanese Whisky page...")
            await page.goto("https://www.thewhiskyexchange.com/c/35/japanese-whisky", wait_until="networkidle")
            await page.wait_for_selector('.product-grid', timeout=20000)

            try:
                cookie_button = page.locator('[data-tid="banner-accept"]')

                await cookie_button.wait_for(state="visible", timeout=5000)
                await cookie_button.click()
                print("Cookie banner accepted and cleared!")

                await page.wait_for_timeout(1000) 
            except Exception:
                print("No cookie banner found (or it timed out). Moving on.")

            button_selector = '.pagination-bar .paging__button'
            click_count = 0
            max_clicks = 30 

            while click_count < max_clicks:
                button = page.locator(button_selector)
                
                if await button.is_visible():
                    print(f"Clicking 'Load More' (Click {click_count + 1})...")

                    await button.scroll_into_view_if_needed()

                    await button.click()
                    click_count += 1

                    delay = random.uniform(2500, 4500)
                    await page.wait_for_timeout(delay) 
                else:
                    print("Button is no longer visible. All products should be loaded!")
                    break

            products = await page.query_selector_all('.product-grid__item')
            print(f"\n--- Total products found on page: {len(products)} ---")
            
            for product in products:
                name_el = await product.query_selector('.product-card__name')
                price_el = await product.query_selector('.product-card__price')
                
                link_el = await product.query_selector('a')
                sku = await link_el.get_attribute('href') if link_el else "UNKNOWN"
                
                if name_el and price_el and sku != "UNKNOWN":
                    name = (await name_el.inner_text()).strip()
                    price = (await price_el.inner_text()).strip()
                    
                    try:
                        db_cursor.execute('''
                            INSERT OR IGNORE INTO products (sku, name, price)
                            VALUES (?, ?, ?)
                        ''', (sku, name, price))
                    except sqlite3.Error as db_err:
                        print(f"Database error on {name}: {db_err}")

            db_conn.commit()
            print("Finished scraping and saving all items to the database.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()
            db_conn.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())