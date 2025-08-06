import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# REMOVED: Unnecessary imports
# from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager
import logging
from datetime import datetime
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
import json

# --- Configuration ---
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# A predefined list of common brands to look for in descriptions
COMPATIBLE_BRAND_LIST = [
    "Whirlpool", "KitchenAid", "Kenmore", "Amana", "Maytag", "Jenn-Air", "Samsung",
    "LG", "GE", "General Electric", "Frigidaire", "Bosch", "Electrolux", "EveryDrop"
]


# --- Scraper Class ---
class StreamlitEcommerceScraper:
    def __init__(self, base_url, use_selenium=False, headless=True, disable_images=True):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.use_selenium = use_selenium
        self.headless = headless
        self.disable_images = disable_images
        self.driver = None
        self.progress_bar = None
        self.status_placeholder = None

        self.selectors = {
            'product_links': ['a[href*="product"]', 'a[href*="/p/"]', '.product-item a', '.product-card a'],
            'name': ['h1', '.product-title', '.product-name'],
            'price': [
                '[itemprop="price"]', '.price-sales', '.product-price .value', '[data-price]',
                '.price-wrapper', '.price', '.product-price', '.current-price', '.sale-price'
            ],
            'sku': ['.sku', '.product-id', '.item-number', "[data-testid='sku']"],
            'brand': ['.brand', '.brand-name', '.manufacturer', '[itemprop="brand"]'],
            'category': ['.breadcrumb', '.category-path'],
            'availability': ['.availability', '.stock-status', "p:contains('Stock')"],
            'description': ['.product-description', '.description', '#description', '[itemprop="description"]'],
            'replaces_models': ["p:contains('is now')", "div:contains('replaces')"],
            'product_details': ['.product-info']
        }

    # --- THIS IS THE CORRECTED FUNCTION ---
    def setup_selenium(self):
        try:
            st.info("🚀 Setting up a lightweight browser instance...")
            chrome_options = Options()
            if self.headless: chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--disable-logging')
            if self.disable_images: chrome_options.add_argument('--blink-settings=imagesEnabled=false')

            # This is the key change:
            # We no longer use webdriver-manager.
            # Selenium will automatically detect the chromedriver that we installed
            # via the packages.txt file in the system's PATH.
            self.driver = webdriver.Chrome(options=chrome_options)

            st.success("✅ Browser is ready!")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            # Provide a more helpful error message for this specific context
            st.error(f"""
            **Selenium setup failed!** This usually means there's an issue with the browser environment.
            - **Error:** {e}
            - **Troubleshooting:** Ensure your `packages.txt` file contains `chromium` and `chromium-driver`.
            """)
            return False

    def get_page_content(self, url):
        try:
            if self.use_selenium and self.driver:
                self.driver.get(url)
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.warning(f"Failed to get content for {url}: {e}")
            return None

    def extract_text(self, soup, selectors):
        if not soup: return ""
        for selector in selectors:
            element = soup.select_one(selector)
            if element: return element.get_text(strip=True)
        return ""

    def clean_price(self, price_text):
        if not price_text: return None
        price_match = re.search(r'[\$€£]*([\d,]+\.?\d*)', str(price_text).replace(',', ''))
        return float(price_match.group(1)) if price_match else None

    def extract_price(self, soup):
        meta_price = soup.select_one('meta[itemprop="price"], meta[property="product:price:amount"]')
        if meta_price and meta_price.get('content'):
            price_val = self.clean_price(meta_price.get('content'))
            if price_val: return price_val

        price_text = self.extract_text(soup, self.selectors['price'])
        return self.clean_price(price_text)

    def extract_specs(self, soup):
        specs = {}
        for dl in soup.select('dl'):
            for dt, dd in zip(dl.select('dt'), dl.select('dd')):
                key, value = dt.get_text(strip=True), dd.get_text(strip=True)
                if key and value: specs[key.replace(':', '')] = value
        for table in soup.select('table.specs-table, table.product-specs'):
            for row in table.select('tr'):
                cells = row.select('th, td')
                if len(cells) == 2:
                    key, value = cells[0].get_text(strip=True), cells[1].get_text(strip=True)
                    if key and value: specs[key.replace(':', '')] = value
        return specs

    def extract_compatible_brands(self, description):
        if not description: return ""
        brands_pattern = re.compile(r'\b(' + '|'.join(COMPATIBLE_BRAND_LIST) + r')\b', re.IGNORECASE)
        found_brands = set(brands_pattern.findall(description))
        return ', '.join(sorted(list(found_brands)))

    def extract_product_data(self, product_url):
        soup = self.get_page_content(product_url)
        if not soup: return None

        data = {'url': product_url, 'scraped_at': datetime.now().isoformat()}
        for key, selectors in self.selectors.items():
            if key not in ['product_links', 'price']:
                data[key] = self.extract_text(soup, selectors)

        data['current_price'] = self.extract_price(soup)
        full_description = f"{data.get('description', '')} {data.get('product_details', '')}"
        data['compatible_brands'] = self.extract_compatible_brands(full_description)
        data.update(self.extract_specs(soup))
        return data

    def discover_product_links(self, url):
        soup = self.get_page_content(url)
        if not soup: return set()
        links = {urljoin(self.base_url, link.get('href').split('?')[0]) for selector in self.selectors['product_links']
                 for link in soup.select(selector) if
                 link.get('href') and self.domain in urljoin(self.base_url, link.get('href'))}
        return links

    def scrape_website(self, max_products=50, max_pages=5):
        if self.use_selenium and not self.setup_selenium(): return []

        if self.status_placeholder: self.status_placeholder.text("🔍 Concurrently discovering product URLs...")

        product_urls, pages_to_scan, scanned_pages = set(), {self.base_url}, set()
        with ThreadPoolExecutor(max_workers=5) as executor:
            for _ in range(max_pages):
                if not pages_to_scan or len(product_urls) >= max_products: break
                current_url = pages_to_scan.pop()
                scanned_pages.add(current_url)

                future = executor.submit(self.discover_product_links, current_url)
                product_urls.update(future.result())

        product_urls_list = list(product_urls)[:max_products]
        if not product_urls_list: return []

        if self.status_placeholder: self.status_placeholder.text(
            f"📦 Found {len(product_urls_list)} products. Starting extraction...")
        if self.progress_bar: self.progress_bar.progress(0)

        products_data = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.extract_product_data, url): url for url in product_urls_list}
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    data = future.result()
                    if data and (data.get('name') or data.get('sku')):
                        products_data.append(data)
                except Exception as e:
                    logger.error(f"Error processing URL {future_to_url[future]}: {e}")

                progress = (i + 1) / len(product_urls_list)
                if self.progress_bar: self.progress_bar.progress(progress)
                if self.status_placeholder: self.status_placeholder.text(
                    f"✅ Scraped {len(products_data)}/{len(product_urls_list)} products")

        return products_data

    def close(self):
        if self.driver: self.driver.quit()


# --- Helper Functions ---
def create_download_link(df, filename, file_format):
    if file_format == 'excel':
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name='Products')
        b64 = base64.b64encode(output.getvalue()).decode()
        return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel File</a>'
    else:
        csv = df.to_csv(index=False).encode('utf-8')
        b64 = base64.b64encode(csv).decode()
        return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'


# --- Streamlit UI Main Function ---
def main():
    st.set_page_config(page_title="High-Speed Scraper", page_icon="⚡", layout="wide")
    st.title("⚡ High-Speed E-commerce Scraper")
    st.markdown("Extracts product data. **New**: Optionally, upload a file to append the new data.")

    st.divider()

    st.subheader("Step 1: Enter the Website to Scrape")
    website_url = st.text_input("Enter a category or product listing URL below.",
                                placeholder="e.g., www.partselect.com/refrigerator-parts/")

    st.subheader("Step 2: Configure Scrape & Export")
    col1, col2 = st.columns(2)
    max_products = col1.number_input("📦 Max products to scrape", 1, 1000, 50)
    max_pages = col2.number_input("📄 Max pages to scan", 1, 50, 5)

    uploaded_file = st.file_uploader(
        "Optional: Upload a CSV/Excel file to append data to",
        type=['csv', 'xlsx']
    )

    with st.expander("🔧 Advanced & Export Options"):
        use_selenium = st.checkbox("Use Browser (Slower)", value=True,
                                   help="Enable for sites that need JavaScript. This is required for deployment on Streamlit Cloud.")
        disable_images = st.checkbox("Disable Images (Faster)", value=True, help="Speeds up browser page loads.")
        file_format = st.radio("Export File Format", ["Excel", "CSV"], horizontal=True)

    st.divider()

    if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
        if not website_url:
            st.error("❌ Please enter a website URL in the box above.")
            return

        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url

        existing_df = None
        if uploaded_file is not None:
            try:
                st.info(f"📄 Reading existing data from `{uploaded_file.name}`...")
                if uploaded_file.name.endswith('.csv'):
                    existing_df = pd.read_csv(uploaded_file)
                else:
                    existing_df = pd.read_excel(uploaded_file)
                st.success("✅ Existing data loaded. New data will be appended.")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                return

        scraper = StreamlitEcommerceScraper(website_url, use_selenium, disable_images=disable_images)
        progress_container = st.empty()
        with progress_container.container():
            scraper.status_placeholder = st.empty()
            scraper.progress_bar = st.progress(0)

        start_time = time.time()
        try:
            products = scraper.scrape_website(int(max_products), int(max_pages))
            if products:
                duration = time.time() - start_time
                new_df = pd.DataFrame(products)

                if existing_df is not None:
                    st.info("Appending new data to the existing file...")
                    final_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    final_df = new_df

                st.success(f"✅ Scraped {len(new_df)} new products in {duration:.2f} seconds! Displaying combined data.")

                final_df.replace('', pd.NA, inplace=True)
                final_df.dropna(axis=1, how='all', inplace=True)
                final_df.fillna("", inplace=True)

                preferred_cols = ['name', 'sku', 'current_price', 'brand', 'compatible_brands', 'availability',
                                  'product_details', 'description', 'url']
                existing_cols_in_df = [col for col in preferred_cols if col in final_df.columns]
                other_cols = sorted([col for col in final_df.columns if col not in existing_cols_in_df])
                final_df = final_df[existing_cols_in_df + other_cols]

                st.dataframe(final_df, use_container_width=True)

                if uploaded_file is not None:
                    filename = uploaded_file.name
                else:
                    domain = urlparse(website_url).netloc.replace('.', '_')
                    ext = 'xlsx' if file_format == 'Excel' else 'csv'
                    filename = f"{domain}_products_{datetime.now():%Y%m%d}.{ext}"

                st.markdown(create_download_link(final_df, filename, file_format.lower()), unsafe_allow_html=True)
            else:
                st.warning(
                    "⚠️ No products found. The site may require the 'Use Browser' option, or the selectors may not match.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
            st.error(f"❌ An unexpected error occurred: {e}")
        finally:
            scraper.close()
            if 'progress_container' in locals():
                progress_container.empty()


if __name__ == "__main__":
    main()