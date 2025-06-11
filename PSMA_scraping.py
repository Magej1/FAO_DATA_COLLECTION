### cd PSMA_DATA
### python -m venv venv
### .\venv\Scripts\activate
# 安装selenium，如果没有 pip install selenium pandas
# python PSMA_scraping.py

import os
import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 设置 Chrome 驱动 ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# --- 获取国家页面内容 ---
def parse_country_data(driver, iso3):
    url = f"https://portlex.fao.org/CountryProfile?{iso3}"
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(random.uniform(2, 3))

    data = {"ISO3": iso3}

    try:
        # 国家名称
        country_name_elem = driver.find_element(By.CSS_SELECTOR, ".page-title h2")
        data["Country Name"] = country_name_elem.text.strip()
    except:
        data["Country Name"] = "N/A"

    try:
        # International Commitments
        commitments = driver.find_elements(By.CSS_SELECTOR, "#intcommit .collection-item")
        data["International Commitments"] = [c.text.strip() for c in commitments]
    except:
        data["International Commitments"] = []

    try:
        # Membership to RFMOs
        rfmo_count = driver.find_element(By.ID, "rfmo_count")
        data["Membership to RFMOs"] = int(rfmo_count.text.strip())
    except:
        data["Membership to RFMOs"] = 0

    try:
        # National Plan of Action
        npoa_count = driver.find_element(By.ID, "npoa_count")
        data["National Plan of Action"] = int(npoa_count.text.strip())
    except:
        data["National Plan of Action"] = 0

    try:
        # Most Relevant Legislation
        mrl_count = driver.find_element(By.ID, "mrl_count")
        data["Most Relevant Legislation"] = int(mrl_count.text.strip())
    except:
        data["Most Relevant Legislation"] = 0

    try:
        # Provisions on PSM
        rows = driver.find_elements(By.CSS_SELECTOR, "#provisionstable tbody tr")
        data["PSM Provisions Count"] = len(rows)
        provision_records = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 6:
                record = {
                    "Countries": cells[0].text.strip(),
                    "Title": cells[1].text.strip(),
                    "Type": cells[2].text.strip(),
                    "Year": cells[3].text.strip(),
                    "Language": cells[4].text.strip(),
                    "Most Relevant": cells[5].text.strip()
                }
                provision_records.append(record)
        data["PSM Provisions"] = provision_records
    except:
        data["PSM Provisions Count"] = 0
        data["PSM Provisions"] = []

    return data

# --- 主程序 ---
def run_scraper(input_csv, output_csv="fao_portlex_data.csv", output_json="fao_portlex_data.json"):
    driver = get_driver()
    df = pd.read_csv(input_csv)
    iso3_list = df["ISO3"].tolist()
    results = []

    for iso3 in iso3_list:
        print(f"🌐 Processing {iso3}...")
        try:
            record = parse_country_data(driver, iso3)
            results.append(record)
        except Exception as e:
            print(f"❌ Error processing {iso3}: {e}")

    driver.quit()

    df_out = pd.DataFrame(results)
    df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {len(results)} countries saved to {output_csv} and {output_json}")

# --- 执行 ---
if __name__ == "__main__":
    run_scraper("sample_iso3_list.csv")
