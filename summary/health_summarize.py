# health_summarize.py

import pandas as pd
import sys
from summarizer import NewsSummarizer

def summarize_news_from_excel(input_file, output_file, prompt):
    df = pd.read_excel(input_file)

    summarizer = NewsSummarizer()

    summaries = []
    for index, row in df.iterrows():
        text = row['본문']

        if pd.notna(text):
            print(f"Processing article {index+1}/{len(df)}...")
            summary = summarizer.summarize_with_gpt(prompt, text)
        else:
            summary = "본문 없음"

        summaries.append(summary)

    df['요약'] = summaries

    # 요약된 결과를 새로운 엑셀 파일로 저장
    df.to_excel(output_file, index=False)
    print(f"요약이 완료되었습니다. 결과는 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("사용법: python summarize_from_excel.py [날짜YYYYMMDD]")
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y%m%d")

    file_prefix = "health"
    with open("../prompt/health_summary.py", 'r', encoding='utf-8') as file:
        prompt = file.read()

    data_directory = "../data/"
    input_path = f"{data_directory}{file_prefix}_{date_str}_naver.xlsx"
    output_path = f"{data_directory}{file_prefix}_{date_str}_summary.xlsx"

    summarize_news_from_excel(input_path, output_path, prompt)
