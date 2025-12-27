import asyncio
import sys
import time

# =================================================
# 🔴 CRITICAL WINDOWS FIX (MUST BE FIRST)
# =================================================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("🚀 Script started", flush=True)

from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

# =================================================
# Pages to extract
# =================================================
URLS = [
    "https://www.playmetrics.site/",
    "https://www.playmetrics.site/docs",
    "https://www.playmetrics.site/about",
    "https://www.playmetrics.site/#Home",
]

# =================================================
# Async scraper function
# =================================================
async def scrape_site():
    print("✅ Entered scrape_site()", flush=True)

    all_links = set()
    all_text_blocks = []

    print("🧠 Launching Playwright...", flush=True)

    async with async_playwright() as p:
        print("🌐 Launching Chromium browser...", flush=True)

        browser = await p.chromium.launch(
            headless=False,   # 👈 IMPORTANT: show browser
            slow_mo=50        # 👈 makes actions visible
        )

        page = await browser.new_page()

        for url in URLS:
            print(f"\n➡️ Visiting: {url}", flush=True)

            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(4000)
            await page.wait_for_load_state("networkidle")

            print("📄 Extracting text...", flush=True)
            text = await page.inner_text("body")

            all_text_blocks.append(
                f"""
==============================
SOURCE URL:
{url}
==============================

{text}
"""
            )

            print("🔗 Extracting links...", flush=True)
            anchors = await page.query_selector_all("a")

            for a in anchors:
                href = await a.get_attribute("href")
                if not href:
                    continue

                full_url = urljoin(url, href)
                parsed = urlparse(full_url)

                if parsed.scheme in ["http", "https"]:
                    clean_url = full_url.split("#")[0]
                    all_links.add(clean_url)

        print("🛑 Closing browser...", flush=True)
        await browser.close()

    # =================================================
    # Save files
    # =================================================
    print("💾 Writing output files...", flush=True)

    joined_text = "\n\n".join(all_text_blocks)
    joined_links = "\n".join(sorted(all_links))

    with open("playmetrics_full_dataset.txt", "w", encoding="utf-8") as f:
        f.write("PLAYMETRICS WEBSITE – EXTRACTED DATASET\n")
        f.write("=====================================\n\n")
        f.write(joined_text)
        f.write("\n\nLINKS\n-----\n")
        f.write(joined_links)

    with open("playmetrics_text_only.txt", "w", encoding="utf-8") as f:
        f.write(joined_text)

    with open("playmetrics_links_only.txt", "w", encoding="utf-8") as f:
        f.write(joined_links)

    print("\n✅ Extraction completed successfully", flush=True)
    print(f"📄 Pages processed: {len(URLS)}", flush=True)
    print(f"🔗 Unique links found: {len(all_links)}", flush=True)
    print("📁 Files created successfully", flush=True)


# =================================================
# Entry point
# =================================================
if __name__ == "__main__":
    print("▶️ Running asyncio loop...", flush=True)
    asyncio.run(scrape_site())
    print("🏁 Script finished", flush=True)
