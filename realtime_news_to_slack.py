import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from api.slack_sender import send_slack_message, format_news_to_message
from urllib.parse import quote

def web_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def build_naver_news_url(query, date):
    encoded_query = quote(query)
    option_date = f"ds={str(int(date[:4]))}.{date[4:6]}.{date[-2:]}&de={date[:4]}.{date[4:6]}.{date[-2:]}"
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sm=tab_opt&sort=1&photo=0&field=0&pd=3&{option_date}"
    return url

def naver_news_scraper(query, date, category):
    url = build_naver_news_url(query, date)
    driver = web_driver()
    news_list = []
    try:
        driver.get(url)
        time.sleep(1)
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
            time_elem = test.find('span', class_='info').text.strip()
            naver_link = test.find_all('a')[-1].get('href') if test and 'naver' in test.find_all('a')[-1].get('href') else None

            # 시간 파싱 및 필터링
            time_delta_minutes = None
            if '분 전' in time_elem:
                time_delta_minutes = int(time_elem.replace('분 전', '').strip())
            elif '시간 전' in time_elem:
                time_delta_minutes = int(time_elem.replace('시간 전', '').strip()) * 60

            if time_delta_minutes is not None and time_delta_minutes <= 3:
                news_list.append({
                    "title": title,
                    "언론사": press,
                    "summary": description,
                    "url": link,
                    "네이버링크": naver_link,
                    "분류": category,
                    "keyword": query,
                    "time": time_elem
                })
    finally:
        driver.quit()

    return news_list

if __name__ == "__main__":
    date = datetime.now().strftime('%Y%m%d')
    selected_keywords = {
        "당사": ["삼성생명", "홍원학"],
        "보험": ["생명보험", "손해보험", "생보", "손보", "보험사기",
                "실손", "무해지", "저해지", "IFRS17", "킥스",
                "삼성화재", "한화생명", "교보생명", "신한라이프"],
        "그룹": ["이재용", "홍라희", "이부진", "이서현", "삼성전자", "삼성물산"],
        "금융": ["금융위", "금감원", "김병환", "이복현", "금융지주"]
    }

    all_news_list = []

    while True:
        for category, keyword_list in selected_keywords.items():
            for query in keyword_list:
                news = naver_news_scraper(query, date, category)
                all_news_list.extend(news)
                if news:
                    message = format_news_to_message(news)
                    send_slack_message("#newsbot-test", message)
                    print(f"슬랙으로 전송된 뉴스: {len(news)}개")

        print("[대기 중 💤] 1분 후 재시작\n")
        time.sleep(60)
