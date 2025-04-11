# naver_news_scraper.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

def read_excel_file(date, prefix):
    filename = f"{prefix}_{date}.xlsx"
    file_path = os.path.join("../data", filename)

    if os.path.exists(file_path):
        df = pd.read_excel(file_path, engine='openpyxl')
        df = df.dropna(subset=['네이버링크'])
        return df
    else:
        print(f"파일이 존재하지 않아요: {file_path}")
        return None

def save_excel_file(df, date, prefix):
    filename = f"{prefix}_{date}_naver.xlsx"
    file_path = os.path.join("../data", filename)
    df.to_excel(file_path, index=False)
    print(f"뉴스 데이터가 {filename} 파일로 저장되었습니다.")

def fetch_article_content(url, headers):
    response = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')

    if 'sports' in url:
        content = soup.find('div', class_='_article_content')
    else:
        content = soup.find('div', id='newsct_article')

    content_text = content.get_text(strip=True) if content else ''
    return content_text, soup

def extract_journalist_info(soup):
    jour = soup.find('div', class_='media_end_head_journalist')
    if jour:
        jour_link_tag = jour.find('a')
        jour_name_tag = jour.find('em', class_='media_end_head_journalist_name')

        jour_link = jour_link_tag.get('href') if jour_link_tag else None
        jour_name = jour_name_tag.get_text(strip=True) if jour_name_tag else None
    else:
        jour_link = jour_name = None

    return jour_link, jour_name


def process_links(links, headers):
    contents, jour_links, jour_names = [], [], []

    for url in links:
        if isinstance(url, str) and url.startswith('http'):
            content_text, soup = fetch_article_content(url, headers)
            contents.append(content_text)

            jour_link, jour_name = extract_journalist_info(soup)
            jour_links.append(jour_link)
            jour_names.append(jour_name)
        else:
            contents.append('')
            jour_links.append('')
            jour_names.append('')

    return contents, jour_links, jour_names

def main():
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = '20250410'
    prefix = '건강' if sys.argv[2] == 'health' else '전체'

    df = read_excel_file(target_date, prefix)

    if df is not None:
        print(f"데이터프레임의 크기: {df.shape}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        links = list(df['네이버링크'])
        contents, jour_links, jour_names = process_links(links, headers)

        df['본문'] = contents
        df['기자명'] = jour_names
        df['기자링크'] = jour_links
        save_excel_file(df, target_date, prefix)
    else:
        print("데이터프레임을 가져올 수 없어서 프로세스를 중지합니다.")

if __name__ == "__main__":
    main()
