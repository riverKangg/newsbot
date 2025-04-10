from promptflow import tool
import requests
import bs4


# @tool
# def fetch_text_content_from_url(url: str):
#     # Send a request to the URL
#     try:
#         headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
#                                  "Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35"}
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             # Parse the HTML content using BeautifulSoup
#             soup = bs4.BeautifulSoup(response.text, 'html.parser')
#             soup.prettify()
#             return soup.get_text()[:2000]
#         else:
#             msg = f"Get url failed with status code {response.status_code}.\nURL: {url}\nResponse: " \
#                   f"{response.text[:100]}"
#             print(msg)
#             return "No available content"
#     except Exception as e:
#         print("Get url failed with error: {}".format(e))
#         return "No available content"



import requests
from bs4 import BeautifulSoup
import bs4

url = 'https://n.news.naver.com/mnews/article/123/0002356709?sid=101'

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


@tool
def fetch_text_content_from_url(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    content_text, soup = fetch_article_content(url, headers)

    jour_link, jour_name = extract_journalist_info(soup)

    return content_text

