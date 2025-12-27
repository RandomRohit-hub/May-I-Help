import asyncio
import sys

# =================================================
# WINDOWS EVENT LOOP FIX (MANDATORY)
# =================================================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urljoin, urlparse

URLS = [
    "https://www.playmetrics.site/",
    "https://www.playmetrics.site/docs",
    "https://www.playmetrics.site/about",
]

async def scrape_site():
    print("🚀 Scraper started", flush=True)

    all_links = set()
    all_text_blocks = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,   # visible for debugging
            slow_mo=30
        )

        context = await browser.new_context()

        for url in URLS:
            print(f"\n➡️ Visiting: {url}", flush=True)

            # ALWAYS create a fresh page per URL
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Wait for visible content instead of fixed timeout
                await page.wait_for_selector("body", timeout=15000)

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

                anchors = await page.query_selector_all("a")
                for a in anchors:
                    href = await a.get_attribute("href")
                    if not href:
                        continue

                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)

                    if parsed.scheme in ["http", "https"]:
                        all_links.add(full_url.split("#")[0])

                print("✅ Page scraped successfully", flush=True)

            except TimeoutError:
                print(f"⚠️ Timeout while loading {url}", flush=True)

            except Exception as e:
                print(f"❌ Error on {url}: {e}", flush=True)

            finally:
                # Close page safely
                if not page.is_closed():
                    await page.close()

        await browser.close()

    # =================================================
    # Save output
    # =================================================
    joined_text = "\n\n".join(all_text_blocks)
    joined_links = "\n".join(sorted(all_links))

    with open("playmetrics_full_dataset.txt", "w", encoding="utf-8") as f:
        f.write("PLAYMETRICS WEBSITE – EXTRACTED DATASET\n")
        f.write("=====================================\n\n")
        f.write(joined_text)
        f.write("\n\nLINKS\n-----\n")
        f.write(joined_links)

    print("\n✅ Extraction completed", flush=True)
    print(f"📄 Pages processed: {len(URLS)}", flush=True)
    print(f"🔗 Unique links: {len(all_links)}", flush=True)


# =================================================
# ENTRY POINT
# =================================================
if __name__ == "__main__":
    asyncio.run(scrape_site())
