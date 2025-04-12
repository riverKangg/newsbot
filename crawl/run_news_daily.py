import subprocess
import sys
from datetime import datetime

def main():
    print("\n📄 사용법: python news_daily.py [health|cnews] [날짜: YYYYMMDD]")

    if len(sys.argv) != 3:
        print("\n❗ 인자 오류: 파일 접두사와 날짜를 정확히 입력해 주세요.")
        sys.exit(1)

    file_prefix = sys.argv[1]
    date_str = sys.argv[2]

    print(f"\n🔍 처리 중인 파일 정보:")
    print(f" - 카테고리 : {file_prefix}")
    print(f" - 날짜     : {date_str}")

    # 뉴스 리스트 스크래핑
    print("📥 1단계: 뉴스 목록 수집 중...")
    subprocess.run(["python3", "news_list_scraper.py", file_prefix, date_str])

    # 네이버 뉴스 스크래핑
    print("📥 2단계: 네이버 뉴스 본문 수집 중...")
    subprocess.run(["python3", "naver_news_scraper.py", file_prefix, date_str])

    print("\n✅ 뉴스 수집 완료!\n")

if __name__ == "__main__":
    main()
