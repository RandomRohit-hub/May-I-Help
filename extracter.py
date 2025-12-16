from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

# Pages to extract
URLS = [
    "https://www.playmetrics.site/",
    "https://www.playmetrics.site/docs",
    "https://www.playmetrics.site/#about"
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

        # 🔹 Extract DOM-based visible text (Framer Motion text)
        text = page.inner_text("body")
        all_text_blocks.append(
            f"\n\n===== SOURCE: {url} =====\n{text}"
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

# ✅ Save extracted text
with open("playmetrics_framer_motion_text.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_text_blocks))

# ✅ Save extracted links
with open("playmetrics_extracted_links.txt", "w", encoding="utf-8") as f:
    for link in sorted(all_links):
        f.write(link + "\n")

print("✅ Extraction completed successfully")
print(f"📄 Total pages processed: {len(URLS)}")
print(f"🔗 Total unique links found: {len(all_links)}")
