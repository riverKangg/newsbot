import subprocess
from datetime import datetime

def main():
    # 오늘 날짜를 YYYYMMDD 형식으로 구하기
    date_today = datetime.now().strftime("%Y%m%d")

    # news_list_scraper.py 실행
    subprocess.run(["python3", "news_list_scraper.py", date_today])

    # naver_news_scraper.py 실행
    subprocess.run(["python3", "naver_news_scraper.py", date_today])

if __name__ == "__main__":
    main()
