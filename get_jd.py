import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

KEYWORDS = ['description', 'job', 'posting', 'content', 'details', 'summary']

def is_dynamic_page(soup):
    # Heuristic: too little content → likely dynamic
    text = soup.get_text(strip=True)
    print(f"Page text length: {len(text)}")
    return len(text) < 400

def extract_best_block(soup):
    candidates = []

    for tag in ['section', 'div', 'article']:
        for match in soup.find_all(tag):
            attrs = (match.get('class') or []) + [match.get('id') or '']
            if any(
                any(kw in str(attr).lower() for kw in KEYWORDS)
                for attr in attrs
            ):
                text = match.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    candidates.append((len(text), text))

    if candidates:
        print(f"✅ Found {len(candidates)} candidate blocks")
        return sorted(candidates, reverse=True)[0][1]
    return None

def extract_job_description_static(url):
    try:
        print("🔍 Trying static scrape...")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        if is_dynamic_page(soup):
            print("⚠️ Detected likely dynamic page")
            return None

        return extract_best_block(soup)

    except Exception as e:
        print(f"❌ Static scrape failed: {e}")
        return None

def extract_job_description_dynamic(url):
    print("🔄 Falling back to dynamic scrape...")
    try:
        options = Options()
        options.add_argument("--headless=new")  # updated headless flag
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.get(url)

        time.sleep(6)  # let JS render

        try:
            # Optional: expand collapsed sections
            see_more = driver.find_elements(By.CLASS_NAME, "show-more-less-html__button--more")
            for btn in see_more:
                try:
                    btn.click()
                    time.sleep(0.5)
                except:
                    continue
        except:
            pass

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return extract_best_block(soup)

    except Exception as e:
        print(f"❌ Dynamic scrape failed: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass

def get_job_description(url):
    print(f"📎 Scraping URL: {url}")
    if not url:
        return "No URL provided."

    # Optional: avoid LinkedIn if needed
    if "linkedin.com/jobs/view" in url:
        print("⚠️ LinkedIn job pages are login-gated. Trying dynamic anyway...")

    # Static first
    desc = extract_job_description_static(url)
    if desc:
        print("✅ Extracted via static scrape")
        return desc

    # Dynamic fallback
    desc = extract_job_description_dynamic(url)
    if desc:
        print("✅ Extracted via dynamic scrape")
        return desc

    return "❌ Could not extract job description."

# 🧪 Example usage:
# description = get_job_description("https://springfinancial.bamboohr.com/careers/261?source=indeed&src=indeed&postedDate=2025-07-25")
# print(description)
