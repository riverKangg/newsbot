# news_kakao_sender.py
#!/usr/bin/env python3

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import openai
import json
import time
import pandas as pd

load_dotenv()

KAKAO_TOKEN = os.getenv("ACCESS_TOKEN")
REST_API_KEY = os.getenv("REST_API_KEY")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

KAKAO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
NAVER_NEWS_URL = "https://news.naver.com/"

HEADERS = {
    "Authorization": f"Bearer {KAKAO_TOKEN}",
    "Content-Type": "application/x-www-form-urlencoded"
}

openai.api_key = OPENAI_API_KEY



class NewsCrawler:
    def __init__(self, news_url, categories):
        self.news_url = news_url
        self.categories = categories

    def crawl(self):
        response = requests.get(self.news_url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_items = []

        for link in soup.select("a"):
            title = link.get_text(strip=True)
            href = link.get("href")
            if not title or not href:
                continue

            for category, keywords in self.categories.items():
                for keyword in keywords:
                    if keyword in title:
                        content = self.get_article_content(href)
                        summary = self.summarize_with_gpt(content)
                        news_items.append({
                            "title": title,
                            "url": href,
                            "keyword": keyword,
                            "category": category,
                            "summary": summary
                        })
                        break

        return news_items

    def get_article_content(self, url):
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")

            content_div = soup.find("div", {"id": "newsct_article"})
            if not content_div:
                paragraphs = soup.find_all("p")
                return " ".join(p.get_text() for p in paragraphs)

            text = content_div.get_text(separator=" ", strip=True)
            return text.strip()
        except Exception as e:
            return "본문 불러오기 실패"

    def summarize_with_gpt(self, text):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                    {"role": "user", "content": f"다음 기사의 내용을 한줄로 요약해줘: {text}"}
                ],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.5,
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print("GPT 요약 오류:", e)
            return "요약 실패"




class NewsBot:
    def __init__(self):
        self.categories = {
            "당사": ["삼성생명", "홍원학"],
            "보험": ["생명보험", "손해보험", "생보", "손보", "보험사기", "실손", "무해지", "저해지", "IFRS17", "킥스",
"삼성화재", "한화생명", "교보생명", "신한라이프"],
            "그룹": ["이재용", "홍라희", "이부진", "이서현", "삼성전자", "삼성물산"],
            "금융": ["금융위", "금감원", "김병환", "이복현", "금융지주"]
        }

        self.news_crawler = NewsCrawler(news_url=NAVER_NEWS_URL, categories=self.categories)
        self.sent_articles = self.load_sent_articles()

    def load_sent_articles(self, filepath="sent_articles.json"):
        try:
            with open(filepath, 'r') as file:
                return set(json.load(file))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def save_sent_articles(self, filepath="sent_articles.json"):
        with open(filepath, 'w') as file:
            json.dump(list(self.sent_articles), file)

    def run(self):
        print("[뉴스봇 실행 중 ⏰]", datetime.now())
        news = self.news_crawler.crawl()

        if not news:
            print("📭 전송할 뉴스 없음")
            return

        results = []

        for item in news:
            self.sent_articles.add(item['url'])
            print(f"📦 기사 저장: {item['title']}")
            results.append(item)

        self.save_sent_articles()

        # 엑셀 파일 저장
        if results:
            df = pd.DataFrame(results)
            date_today = datetime.now().strftime("%Y%m%d")
            file_path = f"../data/daily/news_{date_today}.xlsx"
            df.to_excel(file_path, index=False)
            print(f"🗂 엑셀 파일 저장: {file_path}")

if __name__ == "__main__":
    bot = NewsBot()
    bot.run()
