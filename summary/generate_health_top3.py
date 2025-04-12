import os
import sys
import json
import openai
import pandas as pd
from dotenv import load_dotenv

def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def load_negative_articles(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path)
    if 'label' not in df.columns:
        raise ValueError("'label' column not found in Excel file.")
    return df[df['label'] == True]

def generate_report(prompt: str, articles: pd.DataFrame) -> str:
    article_list = []
    for idx, row in articles.iterrows():
        article_list.append({
            "index": idx,
            "title": row["제목"],
            "summary": row["summary"],
            "content": row["본문"][:100]
        })

    # JSON 형식 문자열로 변환
    formatted_articles = json.dumps(article_list, ensure_ascii=False, indent=2)

    # 전체 프롬프트 구성
    full_prompt = prompt + "\n\n다음은 기사 리스트입니다:\n" + formatted_articles

    # OpenAI API 호출
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 전문 보고서 작성자입니다."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()
def main():
    load_dotenv("../.env")
    openai.api_key = os.getenv("OPENAI_API_KEY")

    print("\n📄 사용법: python generate_report.py [health|cnews] [날짜: YYYYMMDD]")

    if len(sys.argv) != 3:
        print("\n❗ 인자 오류: 파일 접두사와 날짜를 >정확히 입력해 주세요.")
        return

    file_prefix = sys.argv[1]
    date_str = sys.argv[2]

    print(f"\n🔍 처리 중인 파일 정보:")
    print(f" - 카테고리 : {file_prefix}")
    print(f" - 날짜     : {date_str}")

    prompt_path = f"../prompt/{file_prefix}_top3.txt"
    excel_path = f"../data/{file_prefix}_{date_str}_summary.xlsx"

    prompt = load_prompt(prompt_path)
    articles = load_negative_articles(excel_path)

    if articles.empty:
        print("오늘은 부정 기사가 없습니다. 축하합니다 🎉")
        return

    report = generate_report(prompt, articles)
    report_path = f"../data/{file_prefix}_{date_str}_top3.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 부정 기사 리포트가 생성되었습니다: {report_path}")

if __name__ == "__main__":
    main()

