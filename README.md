# ⚡ High-Speed E-commerce Scraper

This is a Streamlit web application designed for high-speed, concurrent scraping of e-commerce websites. It can extract key product information like name, price, SKU, and brand, and it includes logic to find compatible brands and detailed specifications from product descriptions and data tables.

The application allows users to either create a new dataset from a scrape or append the newly scraped data to an existing CSV or Excel file, intelligently matching columns.

![Scraper Screenshot](https://i.imgur.com/your-screenshot-url.png) 
*(Optional: Replace this with a URL to a screenshot of your app)*

## Features

- **High-Speed Scraping**: Uses `ThreadPoolExecutor` for concurrent requests to discover and scrape product pages quickly.
- **Dual Scraping Modes**:
    - **Requests & BeautifulSoup**: A fast, lightweight mode for static websites.
    - **Selenium & Chrome**: A more robust (but slower) browser-based mode for dynamic, JavaScript-heavy sites.
- **Smart Data Extraction**: Uses a list of common CSS selectors to find product data, but is easily configurable.
- **Compatible Brand Detection**: Intelligently parses descriptions to identify and list compatible brands (e.g., Maytag, Whirlpool, GE).
- **Append to Existing File**: Users can upload a CSV or Excel file, and the newly scraped data will be appended to it.
- **Flexible Export**: Download results as either a CSV or an Excel (`.xlsx`) file.
- **User-Friendly Web UI**: Built with Streamlit for a clean and interactive experience.

## Installation

1.  **Clone the repository or download the project files.**

2.  **Set up a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies from the `requirements.txt` file:**
    ```bash
    pip install -r requirements.txt
    ```
    This will install all necessary libraries, including Streamlit, Pandas, Selenium, and `openpyxl` for Excel support.

## How to Run the Application

1.  Make sure you have installed all the packages from `requirements.txt`.
2.  Open your terminal or command prompt and navigate to the project directory.
3.  Run the following command:
    ```bash
    streamlit run your_script_name.py
    ```
    (Replace `your_script_name.py` with the actual name of your Python file).

4.  The application will open automatically in your web browser.

## How to Use the App

1.  **Enter URL**: Paste the URL of an e-commerce category or product listing page into the "Step 1" input box.
2.  **Configure Settings**:
    - Adjust the maximum number of products to scrape and pages to scan.
    - **(Optional)** Upload an existing CSV or Excel file if you wish to append the new data to it.
3.  **Advanced Options**:
    - **Use Browser (Slower)**: Check this box if the target website loads its content dynamically using JavaScript. The app will use Selenium to control a headless Chrome browser.
    - **Export Format**: Choose whether to download the final data as an Excel or CSV file.
4.  **Start Scraping**: Click the "Start Scraping" button to begin the process. The app will show a progress bar and status updates.
5.  **Download**: Once finished, a data table will display the results, and a download link will appear.

## Disclaimer

This tool is intended for educational purposes and for scraping publicly available data. Please be respectful of the websites you scrape and be sure to review their `robots.txt` file and terms of service. Do not use this tool for any malicious activities. The developers are not responsible for any misuse of this application.