# naver_news_scraper.py

import requests
from bs4 import BeautifulSoup

import pandas as pd
import os

def read_excel_file(date):
    # 파일명이 "네이버뉴스_삼성생명_YYYYMMDD" 형식이므로 문자열을 이용해 파일명 생성
    filename = f"네이버뉴스_전체_{date}.xlsx"
    file_path = os.path.join("./data", filename)

    if os.path.exists(file_path):
        df = pd.read_excel(file_path, engine='openpyxl')
        df = df.dropna(subset=['네이버링크'])
        return df
    else:
        print(f"파일이 존재하지 않아요: {file_path}")
        return None

def save_excel_file(date):
    filename = f"네이버뉴스_전체_{date}_2.xlsx"
    df.to_excel(filename, index=False)
    print(f"뉴스 데이터가 {filename} 파일로 >저장되었습니다.")



target_date = '20250410'#input("날짜를 YYYYMMDD 형식으로 입력하세요: ")
df = read_excel_file(target_date)
print(df.shape)

# HTTP 요청
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

contents = []
links = list(df['네이버링크'])
jour_links = []
jour_names = []

for url in links:
    if isinstance(url, str) and url.startswith('http'):
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if 'sports' in url:
            content = soup.find('div', class_='_article_content')
        else:
            content = soup.find('div', id='newsct_article')
        
        if content:
            content_text = content.get_text(strip=True)
            contents.append(content_text)

        jour = soup.find('div', class_='media_end_head_journalist')
        if jour:
            jour_link_tag = jour.find('a')
            jour_name_tag = jour.find('em', class_='media_end_head_journalist_name')

            # null-safe 체크
            jour_link = jour_link_tag.get('href') if jour_link_tag else None
            jour_name = jour_name_tag.get_text(strip=True) if jour_name_tag else None

            jour_links.append(jour_link)
            jour_names.append(jour_name)
    else:
        contents.append('')
        jour_links.append('')
        jour_names.append('')

print(f"df 길이: {len(df)}, contents 길이: {len(contents)}")  # 여기서 꼭 확인!!
df['본문'] = contents
df['기자명'] = jour_names
df['기자링크'] = jour_links
save_excel_file(target_date)
