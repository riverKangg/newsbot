# naver_news_one.py
# 네이버뉴스 한개만

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

def fetch_article_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
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

def process_link(link):
    content_text, soup = fetch_article_content(link)
    jour_link, jour_name = extract_journalist_info(soup)
    return content_text, jour_link, jour_name

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("test url")
        url = "https://n.news.naver.com/mnews/article/020/0003627641?sid=103"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    content, jour_link, jour_name = process_link(url)
    print("본문:", content)
    print("기자 링크:", jour_link)
    print("기자 이름:", jour_name)

if __name__ == "__main__":
    main()
