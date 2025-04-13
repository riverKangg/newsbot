# news_list_scraper2.py

import os
import sys
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
    options.add_argument('--headless=new')  # 최신 버전용!

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')  # crash 방지용

    service = Service(ChromeDriverManager(driver_version="129.0.6668.59").install())

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def build_naver_news_url(query, date):
    encoded_query = quote(query)
    option_date = f"ds={str(int(date[:4]))}.{date[4:6]}.{date[-2:]}&de={date[:4]}.{date[4:6]}.{date[-2:]}"
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
            press = press.replace("언론사 선정","")
            desc_elem = item.select_one(".dsc_txt_wrap")
            description = desc_elem.text.strip() if desc_elem else "요약 정보 없음"

            test = item.find("div", class_="info_group")
            naver_link = test.find_all('a')[-1].get('href') if 'naver' in test.find_all('a')[-1].get('href') else None

            news_list.append({
                "제목": title,
                "언론사": press,
                # "요약": description,
                "링크": link,
                "네이버링크": naver_link,
                "분류": category,
                "키워드": query  # 각 뉴스 항목에 해당 키워드 추가
            })
    finally:
        driver.quit()

    return news_list

def save_to_excel(file_prefix, all_news_list, date):
    if all_news_list:
        data_directory = "../data/"
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
        df = pd.DataFrame(all_news_list)
        df = df[~df['제목'].str.contains('운세')]
        if file_prefix=='health':
            desired_press = ['조선일보', '중앙일보','동아일보','한국경제','매일경제']
            df = df[df['언론사'].isin(desired_press)]
        filename = f"{data_directory}{file_prefix}_{date}.xlsx"
        df.to_excel(filename, index=False)
        print(f"뉴스 데이터가 {filename} 파일로 저장되었습니다.")

if __name__ == "__main__":
    print("\n📄 사용법: python news_list_scraper.py [health|cnews] [날짜: YYYYMMDD]")

    if len(sys.argv) != 3:
        print("\n❗ 인자 오류: 파일 접두사와 날짜를 정확히 입력해 주세요.")
        sys.exit(1) 

    file_prefix = sys.argv[1]
    date_str = sys.argv[2]

    if file_prefix=='health':
        selected_keywords = {
            "질병/건강": [
                "당뇨", "고혈압", "치매", "암", "심장", "뇌졸중",
                "갑상선", "위암", "유방암", "대상포진",
                "골다공증", "간경화", "폐렴"
            ],
            "예방/생활습관": ["건강검진", "예방접종", "운동", "식습관",
                "금연", "절주", "생활습관병", "스트레스", "수면"],
            "노령화/고령층": ["노인", "고령자", "노후", "시니어", "60대", "70대", "요양병원",
"장기요양", "간병"]
        }
    elif file_prefix=='cnews':
        selected_keywords = {
            "당사": ["삼성생명", "홍원학"],
            "보험": ["생명보험", "손해보험", "생보", "손보", "보험사기",
                    "실손", "무해지", "저해지", "IFRS17", "킥스",
                    "삼성화재", "한화생명", "교보생명", "신한라이프"],
            "그룹": ["이재용", "홍라희", "이부진", "이서현", "삼성전자", "삼성물산"],
            "금융": ["금융위", "금감원", "김병환", "이복현", "금융지주"]
        }

    all_news_list = []

    for category, keyword_list in selected_keywords.items():
        for query in keyword_list:
            news = naver_news_scraper(query, date_str, category)
            all_news_list.extend(news)

    save_to_excel(file_prefix, all_news_list, date_str)
