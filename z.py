from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

url = "https://www.playmetrics.site/"

all_links = set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=60000)
    page.wait_for_load_state("networkidle")

    # ✅ Extract all visible text
    content = page.inner_text("body")

    # ✅ Extract all anchor links
    anchors = page.query_selector_all("a")
    for a in anchors:
        href = a.get_attribute("href")
        if href:
            full_url = urljoin(url, href)
            # keep only valid HTTP links
            if urlparse(full_url).scheme in ["http", "https"]:
                all_links.add(full_url.split("#")[0])

    browser.close()

# ✅ Save rendered text
with open("website_rendered_text.txt", "w", encoding="utf-8") as f:
    f.write(content)

# ✅ Save extracted links
with open("website_links.txt", "w", encoding="utf-8") as f:
    for link in sorted(all_links):
        f.write(link + "\n")

print("Extraction completed")
print(f"Total links found: {len(all_links)}")
