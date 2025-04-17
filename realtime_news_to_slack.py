import os
import re
import sys
import json
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import quote

from summary.summarizer import NewsSummarizer
from crawl.naver_news_one import process_link
from api.slack_sender import send_slack_message, format_news_to_message

with open(f"./prompt/cnews_summary.txt", 'r',encoding='utf-8') as file:
    prompt = file.read()
news_sources = [
    # 종합지
    "조선일보", "중앙일보", "동아일보", "한국일보", "국민일보", "서울신문", "세계일보",
    "한겨레", "경향신문", "문화일보", "헤럴드경제", "아시아경제", "내일신문",
    "매일경제", "한국경제", "서울경제", "머니투데이", "파이낸셜뉴스", "이데일리",
    "아주경제", "메트로경제",

    # 방송사
    "KBS", "MBC", "SBS", "JTBC", "TV조선", "채널A", "MBN", "연합뉴스TV", "YTN",
    "SBS Biz", "한경TV", "매일경제TV", "MTN", "CBS",

    # 통신사 및 전문지
    "연합뉴스", "연합인포맥스", "뉴시스", "뉴스1", "더벨", "이투데이", "뉴스토마토",
    "에너지경제", "브릿지경제", "매일일보", "아시아타임즈", "전자신문", "조선비즈",
    "머니S", "디지털타임스", "소비자가 만드는 신문", "청년일보", "CEO스코어데일리",
    "EBN", "FETV", "굿모닝경제", "글로벌이코노믹", "뉴데일리", "뉴스웨이", "뉴스핌",
    "데일리안", "대한경제", "비즈니스포스트", "아시아투데이", "쿠키뉴스", "매경닷컴",
    "한경닷컴",

    # 보험 및 금융 전문지
    "한국보험신문", "보험신보", "보험매일", "보험저널", "비즈워치", "파이낸셜투데이",
    "서울파이낸스", "대한금융신문", "한국금융", "금융경제"
]

def generate_random_phone_number():
    middle = random.randint(1000, 9999)
    last = random.randint(1000, 9999)
    return f"010-{middle}-{last}"

def parse_response(response):
    try:
        # 여러 번 나누어진 응답을 하나로 합치기
        if isinstance(response, list):
            response = "".join(response)
        
        # 마크다운 코드 블록 제거
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1]
        if '```' in response:
            response = response.split('```')[0]
        response = response.strip()
        
        # JSON 문자열 정규화
        response = response.replace('\n', ' ').replace('\r', '')
        response = re.sub(r'\s+', ' ', response)
        response = response.replace('False','false').replace('True','true')
        response = re.sub("'", '', response)

        # 중복된 JSON 응답 제거
        if response.count('{') > 1:
            # 마지막 완전한 JSON 객체만 사용
            last_brace = response.rfind('}')
            if last_brace != -1:
                response = response[:last_brace+1]
        
        # JSON 파싱
        result = json.loads(response)
        print(result)
        
        # 필수 필드가 없는 경우 기본값 설정
        if 'is_related' not in result:
            result['is_related'] = False
        if 'label' not in result:
            result['label'] = 'False'
        if 'summary' not in result:
            result['summary'] = '요약 실패'
            
        # label 값이 예상된 형식이 아닌 경우 수정
        if isinstance(result['label'], bool):
            result['label'] = 'True' if result['label'] else 'False'
        elif result['label'] not in ['True', 'False', 'Positive', 'Negative', 'Neutral']:
            result['label'] = 'False'
            
        return result
    except Exception as e:
        print(f"Unexpected error in parse_response: {e}")
        print(f"Raw response: {response}")
        return {
            'is_related': False,
            'label': 'Neutral',
            'summary': '요약 실패'
        }

def process_content_with_prompt(content, prompt):
    try:
        summarizer = NewsSummarizer()
        sentdict_raw = summarizer.summarize_with_gpt(content, prompt)
        sentdict = parse_response(sentdict_raw)

        if sentdict is None:
            raise ValueError("Parsed dictionary is None.")

        is_related = sentdict.get('is_related', False)
        label = sentdict.get('label')
        summary = sentdict.get('summary')

        return is_related, label, summary
    except Exception as e:
        print(f"Error in process_content_with_prompt: {str(e)}")
        print(f"Content: {content[:100]}...")  # 첫 100자만 로깅
        return False, "False", "요약 실패"

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
    print(f"🔍 검색 시작 - 카테고리: '{category}', 키워드: '{query}'")
    url = build_naver_news_url(query, date)
    driver = web_driver()
    results = [] 
    try:
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news_items = soup.select(".news_area")
        print(f"📰 발견된 뉴스 수: {len(news_items)}")
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
            if naver_link is not None:
                print(f"🔗 기사 링크 분석 중: {naver_link}")

                # 시간 파싱 및 필터링
                time_delta_minutes = None
                if '분 전' in time_elem:
                    time_delta_minutes = int(time_elem.replace('분 전', '').strip())
                elif '시간 전' in time_elem:
                    time_delta_minutes = int(time_elem.replace('시간 전', '').strip()) * 60

                content, jour_link, jour_name = process_link(naver_link)
                summarizer = NewsSummarizer()
                is_related, label, summary = process_content_with_prompt(content, prompt)
 
                print(f"📊 분석 결과:")
                print(f"  - 관련성: {is_related}")
                print(f"  - 감정: {label}")
                print(f"  - 요약: {summary}")
                print(f"  - 기자: {jour_name}")
                print(f"  - 기자 링크: {jour_link}")
 
                if label == "Negative" and time_delta_minutes is not None and time_delta_minutes <= 2:
                    random_phone_number = generate_random_phone_number() if press in news_sources else None

                    news_item = {
                        "category": category,
                        "keyword": query,
                        "title": title,
                        "press": press,
                        "description": description,
                        "url": link,
                        "naver_link": naver_link,
                        "time": time_elem,
                        "content": content,
                        "jour_name": jour_name,
                        "sentiment_label": sentiment_label,
                        "phone_number" : random_phone_number,
                        "neg_sent" : neg_sent
                    }
                    message = format_news_to_message(news_item)
                    send_slack_message("#news-feed", message)
                    print(f"📤 슬랙으로 전송 완료 - 제목: '{title}'")
                    results.append(news_item)
    finally:
        driver.quit()
    return results

if __name__ == "__main__":
    date = datetime.now().strftime('%Y%m%d')
    selected_keywords = {
        "test": ["윤석열"],
        "당사": ["삼성생명", "홍원학"],
        "보험": ["생명보험", "손해보험", "생보", "손보", "보험사기",
                "실손", "무해지", "저해지", "IFRS17", "킥스",
                "삼성화재", "한화생명", "교보생명", "신한라이프"],
        "그룹": ["이재용", "홍라희", "이부진", "이서현", "삼성전자", "삼성물산"],
        "금융": ["금융위", "금감원", "김병환", "이복현", "금융지주"]
    }

    while True:
        for category, keyword_list in selected_keywords.items():
            for query in keyword_list:
                naver_news_scraper(query, date, category)

        print("[대기 중 💤] 1분 후 재시작\n")
        time.sleep(60)
