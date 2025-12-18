from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

# Pages to extract
URLS = [
    "https://www.playmetrics.site/",
    "https://www.playmetrics.site/docs",
    "https://www.playmetrics.site/about",
    "https://www.playmetrics.site/#Home",
    
]

all_links = set()
all_text_blocks = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for url in URLS:
        print(f"Visiting: {url}")

        page.goto(url, timeout=60000)

        # 🔹 Allow Framer Motion animations to complete
        page.wait_for_timeout(4000)
        page.wait_for_load_state("networkidle")

        # 🔹 Extract DOM-based visible text
        text = page.inner_text("body")

        all_text_blocks.append(
            f"""
==============================
SOURCE URL:
{url}
==============================

{text}
"""
        )

        # 🔹 Extract all links
        anchors = page.query_selector_all("a")
        for a in anchors:
            href = a.get_attribute("href")
            if not href:
                continue

            full_url = urljoin(url, href)
            parsed = urlparse(full_url)

            if parsed.scheme in ["http", "https"]:
                clean_url = full_url.split("#")[0]
                all_links.add(clean_url)

    browser.close()

# 🔹 Join all text into one block
joined_text = "\n\n".join(all_text_blocks)

# 🔹 Join links into one block
joined_links = "\n".join(sorted(all_links))

# ✅ Save ONE combined dataset file (BEST for RAG / ML)
with open("playmetrics_full_dataset.txt", "w", encoding="utf-8") as f:
    f.write("PLAYMETRICS WEBSITE – EXTRACTED DATASET\n")
    f.write("=====================================\n\n")

    f.write("TEXT CONTENT\n")
    f.write("------------\n")
    f.write(joined_text)

    f.write("\n\nLINKS\n")
    f.write("-----\n")
    f.write(joined_links)

# (Optional) Save separate files as well
with open("playmetrics_text_only.txt", "w", encoding="utf-8") as f:
    f.write(joined_text)

with open("playmetrics_links_only.txt", "w", encoding="utf-8") as f:
    f.write(joined_links)

print("✅ Extraction completed successfully")
print(f"📄 Total pages processed: {len(URLS)}")
print(f"🔗 Total unique links found: {len(all_links)}")
print("📁 Files created:")
print("   - playmetrics_full_dataset.txt")
print("   - playmetrics_text_only.txt")
print("   - playmetrics_links_only.txt")
