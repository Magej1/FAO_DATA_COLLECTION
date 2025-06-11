### cd PSMA_DATA
### python -m venv venv
### .\venv\Scripts\activate
# 安装selenium，如果没有 pip install selenium pandas
# python PSMA_scraping_1.py

### PSMA_scraping_1.py
# 用于抓取 FAO PortLex 各国渔业政策信息（支持断点续抓、动态内容加载）

import pandas as pd
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# =====================
# 初始化 Chrome 驱动
# =====================
# def get_driver():
    # options = Options()
    # # options.add_argument("--headless")  # 可调试时关闭 headless
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # driver_path = "D:/文档/DataScience/chromedriver.exe"  # 修改为你的 chromedriver 路径
    # service = Service(driver_path)
    # return webdriver.Chrome(service=service, options=options)

def get_driver(): # 新版加了代理
    options = Options()
    # options.add_argument("--headless")  # 调试阶段建议关闭 headless
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    
    # 添加用户代理模拟真实浏览器（重点！）
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    driver_path = "D:/文档/DataScience/chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# =============================
# 解析每个国家页面的数据逻辑
# =============================
def parse_country_page(driver, iso3):
    url = f"https://portlex.fao.org/CountryProfile?{iso3}"
    driver.get(url)

    # ✅ 等待整个页面加载完毕
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(2)  # 给 JavaScript 渲染一点时间

    # ✅ 再等待你需要的数据区域加载出来（可选增强稳定性）
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".header-parent-item span"))
    )

    # ✅ 之后再抓取页面 HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 以下内容不变 ↓↓↓
    country_name_tag = soup.select_one(".header-parent-item span")
    country_name = country_name_tag.get_text(strip=True) if country_name_tag else "N/A"

    intl_commitments = [a.get_text(strip=True) for a in soup.select(".treaties_div a")]
    rfmo_count = len(soup.select("ul.rfmo .collapsible-body a"))
    npoa_count = len(soup.select("ul.national_plans .collapsible-body a"))
    mrl_count = len(soup.select("ul.most_relevant .collapsible-body a"))

    psm_section = soup.select_one(".query_results_count span")
    try:
        psm_count = int(psm_section.get_text(strip=True)) if psm_section else 0
    except:
        psm_count = 0

    psm_records = []
    for record in soup.select(".result-list .parent-item-container"):
        psm_entry = {}
        rows = record.select("table tr")
        for row in rows:
            tds = row.select("td")
            if len(tds) == 2:
                key = tds[0].get_text(strip=True)
                val = tds[1].get_text(strip=True)
                psm_entry[key] = val
        psm_records.append(psm_entry)

    return {
        "ISO3": iso3,
        "Country Name": country_name,
        "International Commitments": intl_commitments,
        "Membership to RFMOs": rfmo_count,
        "National Plan Of Action": npoa_count,
        "Most Relevant Legislation": mrl_count,
        "PSM Provisions Count": psm_count,
        "PSM Provisions": psm_records
    }


# =====================
# 主程序
# =====================
def run_scraper(iso3_csv="sample_iso3_list_TEST.csv", output_csv="fao_portlex_data_TEST.csv", output_json="fao_portlex_data_TEST.json"): ### 修改为你的 ISO3 列表文件路径和输出文件路径
    df_iso3 = pd.read_csv(iso3_csv)
    processed = []

    try:
        existing_df = pd.read_csv(output_csv)
        done_set = set(existing_df["ISO3"].astype(str))
        print(f"🔁 Resuming from last point. Already processed {len(done_set)} countries.")
    except:
        existing_df = pd.DataFrame()
        done_set = set()

    driver = get_driver()

    for iso3 in df_iso3["ISO3"].astype(str):
        if iso3 in done_set:
            continue

        print(f"🌐 Processing {iso3}...")
        try:
            result = parse_country_page(driver, iso3)
            processed.append(result)

            df_new = pd.DataFrame(processed)
            df_all = pd.concat([existing_df, df_new], ignore_index=True)
            df_all.to_csv(output_csv, index=False, encoding="utf-8-sig")

            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(df_all.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

            processed = []

        except Exception as e:
            print(f"❌ Error processing {iso3}: {e}")
            continue

    driver.quit()
    print(f"\n✅ Done. Output saved to {output_csv} and {output_json}")

# ============
# 启动程序
# ============
if __name__ == "__main__":
    run_scraper("sample_iso3_list_TEST.csv") ####### 修改为你的 ISO3 列表文件路径
