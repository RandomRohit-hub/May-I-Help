from playwright.sync_api import sync_playwright

URLS = [
      "https://www.playmetrics.site/",
    "https://www.playmetrics.site/docs",
    "https://www.playmetrics.site/about",
    "https://www.playmetrics.site/#Home",
    
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    all_text = []

    for url in URLS:
        page.goto(url)
        page.wait_for_timeout(3000)

        text = page.inner_text("body")
        all_text.append(f"\n--- {url} ---\n{text}")

    browser.close()

with open("website_text.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_text))

print("Done")
