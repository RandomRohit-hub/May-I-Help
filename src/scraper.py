import os
import json
import logging
from playwright.sync_api import sync_playwright
from src.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebsiteScraper:
    def __init__(self, urls):
        self.urls = urls
        self.output_dir = Config.DATA_DIR
        self.output_file = os.path.join(self.output_dir, "scraped_data.json")
        os.makedirs(self.output_dir, exist_ok=True)

    def scrape(self):
        scraped_data = []
        with sync_playwright() as p:
            logger.info("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for url in self.urls:
                try:
                    logger.info(f"Scraping: {url}")
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # Wait a bit for any dynamic content
                    page.wait_for_timeout(2000)
                    
                    title = page.title()
                    content = page.inner_text("body")
                    
                    scraped_data.append({
                        "url": url,
                        "title": title,
                        "content": content
                    })
                    logger.info(f"Successfully scraped {url}")
                    
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")

            browser.close()

        self._save_data(scraped_data)
        logger.info(f"Scraping completed. Data saved to {self.output_file}")

    def _save_data(self, data):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # URL list from original project
    URLS = [
        "https://www.playmetrics.site/",
        "https://www.playmetrics.site/docs",
        "https://www.playmetrics.site/about",
        "https://www.playmetrics.site/#Home",
    ]
    
    scraper = WebsiteScraper(URLS)
    scraper.scrape()
