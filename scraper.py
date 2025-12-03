from tqdm import tqdm

from trade_util import Country, Product, TradeFlow, UnitType
import os
import itertools

from playwright.sync_api import sync_playwright, Browser


def downloader(product: Product, country: Country, trade_flow: TradeFlow, unit_type: UnitType, browser: Browser):
    output_path = f"out/{trade_flow.name.lower()}/{product.value}/{unit_type.name.lower()}/{country.name}.txt"
    if country.code in ("344", "566", "591") or os.path.exists(output_path):
        return

    page = browser.new_page()

    try:
        url = f"https://www.trademap.org/Country_SelProductCountry_TS.aspx?nvpm=1|{country.code}||||{product.get_value()}|||4|1|1|{trade_flow.get_value()}|2|1|2|{unit_type.get_value()}|1|1"

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        page.select_option("#ctl00_PageContent_GridViewPanelControl_DropDownList_NumTimePeriod", "20")
        page.select_option("#ctl00_PageContent_GridViewPanelControl_DropDownList_PageSize", "300")

        page.wait_for_load_state("networkidle")

        with page.expect_download() as download_info:
            page.click("#ctl00_PageContent_GridViewPanelControl_ImageButton_Text")

        download = download_info.value
        download.save_as(output_path)

    except Exception as e:
        print(e)
        print("Exception while fetching data")

    page.close()


def scrape_all():
    all_flows = list(TradeFlow)
    all_products = list(Product)
    all_countries = list(Country.loader("countries.json"))
    all_types = list(UnitType)

    combinations = list(itertools.product(all_flows, all_products, all_countries, all_types))
    total = len(combinations)

    print(f"Products:   {len(all_products)}")
    print(f"Countries:  {len(all_countries)}")
    print(f"Flows:      {len(all_flows)}")
    print(f"Unit types: {len(all_types)}")
    print(f"Total combinations: {total}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # tqdm progress bar
        for flow, product_item, country, type_item in tqdm(combinations, desc="Scraping", unit="task"):
            print(f"Processing {flow.name} | {product_item.name} | {country.name} | {type_item.name}")

            downloader(
                product=product_item,
                country=country,
                trade_flow=flow,
                unit_type=type_item,
                browser=browser
            )

        browser.close()

if __name__ == '__main__':
    scrape_all()
