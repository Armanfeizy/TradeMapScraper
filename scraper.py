import asyncio
import time
import os
from dataclasses import dataclass
from playwright.async_api import async_playwright
from trade_util import Country, Product, TradeFlow, UnitType
import itertools


def get_path(product: Product, country: Country, flow: TradeFlow, unit_type: UnitType):
    return f"out/{flow.name.lower()}/{product.value}/{unit_type.name.lower()}/{country.name}.txt"


@dataclass
class LogEvent:
    wid: int
    msg: str


# ---------------- WORKER ---------------- #
async def worker(wid, task_q, log_q):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        await log_q.put(LogEvent(wid, "started"))

        while True:
            task = await task_q.get()
            if task is None:
                break

            flow, product_item, country, type_item = task
            output_path = get_path(product_item, country, flow, type_item)

            url = (
                f"https://www.trademap.org/Country_SelProductCountry_TS.aspx?"
                f"nvpm=1|{country.code}||||{product_item.get_value()}|||4|1|1|"
                f"{flow.get_value()}|2|1|2|{type_item.get_value()}|1|1"
            )

            await log_q.put(LogEvent(wid, f"scraping {country.name} {product_item.value} {flow.get_value()} {type_item.get_value()}"))

            try:
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                await page.select_option(
                    "#ctl00_PageContent_GridViewPanelControl_DropDownList_NumTimePeriod", "20"
                )
                await page.select_option(
                    "#ctl00_PageContent_GridViewPanelControl_DropDownList_PageSize", "300"
                )

                await page.wait_for_load_state("networkidle")

                async with page.expect_download() as d:
                    await page.click("#ctl00_PageContent_GridViewPanelControl_ImageButton_Text")

                download = await d.value
                await download.save_as(output_path)

                await log_q.put(LogEvent(wid, f"done {country.name}/{product_item.value}"))

                await page.close()

            except Exception as e:
                await log_q.put(LogEvent(wid, f"ERROR {country.name}/{product_item.value}: {e}"))

            task_q.task_done()

        await browser.close()


# ---------------- LOGGER ---------------- #
async def logger(log_q):
    while True:
        ev = await log_q.get()
        print(f"[W{ev.wid}] {ev.msg}")
        log_q.task_done()


# ---------------- PROGRESS ---------------- #
async def progress(task_q, total):
    start = time.time()
    while True:
        done = total - task_q.qsize()
        elapsed = time.time() - start
        speed = done / elapsed if elapsed else 0
        eta = (task_q.qsize() / speed) if speed else 9999

        print(f"[PROGRESS] {done}/{total} | ETA {eta:.1f}s")
        await asyncio.sleep(1)


# ---------------- MAIN ---------------- #
async def main(num_workers=4):
    task_q = asyncio.Queue()
    log_q = asyncio.Queue()

    all_flows = list(TradeFlow)
    all_products = list(Product)
    all_countries = list(Country.loader("countries.json"))
    all_types = list(UnitType)

    # ---- Build tasks (real TradeMap arguments) ---- #
    for flow, product_item, country, type_item in itertools.product(all_flows, all_products, all_countries, all_types):
        if country.code in ("344", "566", "591"):
            continue
        path = get_path(product_item, country, flow, type_item)
        if not os.path.exists(path):
            task_q.put_nowait((flow, product_item, country, type_item))

    total = task_q.qsize()
    print(f"Total tasks: {total}")

    # start logger + progress
    asyncio.create_task(logger(log_q))
    asyncio.create_task(progress(task_q, total))

    # start workers
    workers = [asyncio.create_task(worker(i, task_q, log_q)) for i in range(num_workers)]

    await task_q.join()

    # tell workers to stop
    for _ in workers:
        task_q.put_nowait(None)

    await asyncio.gather(*workers)


if __name__ == "__main__":
    asyncio.run(main(num_workers=8))
