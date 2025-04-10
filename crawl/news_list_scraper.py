# /Users/samsung/Documents/hackathon/NaverNewsCrawler/newsbot/naver_scraper.py

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote

def web_driver():
    options = Options()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def build_naver_news_url(query, date):
    encoded_query = quote(query)
    option_date = f"ds={date[:4]}.{date[4:6]}.{date[-2:]}&de={date[:4]}.{date[4:6]}.{date[-2:]}"
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&{option_date}"
    print(url)
    return url

def scroll_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def naver_news_scraper(query, date, category):
    url = build_naver_news_url(query, date)
    driver = web_driver()
    news_list = []
    try:
        driver.get(url)
        time.sleep(1)
        scroll_down(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news_items = soup.select(".news_area")
        for item in news_items:
            title_elem = item.select_one(".news_tit")
            title = title_elem.text.strip()
            link = title_elem["href"]
            press_elem = item.select_one(".info.press")
            press = press_elem.text.strip() if press_elem else "언론사 정보 없음"
            desc_elem = item.select_one(".dsc_txt_wrap")
            description = desc_elem.text.strip() if desc_elem else "요약 정보 없음"

            test = item.find("div", class_="info_group")
            naver_link = test.find_all('a')[-1].get('href') if 'naver' in test.find_all('a')[-1].get('href') else None

            news_list.append({
                "제목": title,
                "언론사": press,
                "요약": description,
                "링크": link,
                "네이버링크": naver_link,
                "분류": category,
                "키워드": query  # 각 뉴스 항목에 해당 키워드 추가
            })
    finally:
        driver.quit()

    return news_list

def save_to_excel(all_news_list, date):
    if all_news_list:
        data_directory = "data/"
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
        df = pd.DataFrame(all_news_list)
        filename = f"{data_directory}네이버뉴스_전체_{date}.xlsx"
        df.to_excel(filename, index=False)
        print(f"뉴스 데이터가 {filename} 파일로 저장되었습니다.")

if __name__ == "__main__":
    date = '20250409'
    keywords = {
        "당사": ["삼성생명", "홍원학"],
        "보험": ["생명보험", "손해보험", "생보", "손보", "보험사기",
                "실손", "무해지", "저해지", "IFRS17", "킥스",
                "삼성화재", "한화생명", "교보생명", "신한라이프"],
        "그룹": ["이재용", "홍라희", "이부진", "이서현", "삼성전자", "삼성물산"],
        "금융": ["금융위", "금감원", "김병환", "이복현", "금융지주"]
    }

    all_news_list = []

    for category, keyword_list in keywords.items():
        for query in keyword_list:
            news = naver_news_scraper(query, date, category)
            all_news_list.extend(news)

    save_to_excel(all_news_list, date)
