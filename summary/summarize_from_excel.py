import pandas as pd
from summarizer import NewsSummarizer

# 엑셀 데이터 프레임 읽기 및 요약 생성
def summarize_news_from_excel(input_file, output_file):
    # 엑셀 파일 읽기
    df = pd.read_excel(input_file)

    # NewsSummarizer 인스턴스 생성
    summarizer = NewsSummarizer()

    # 요약 생성 및 "요약" 컬럼에 추가
    summaries = []
    for index, row in df.iterrows():
        text = row['본문']

        if pd.notna(text):
            print(f"Processing article {index+1}/{len(df)}...")
            summary = summarizer.summarize_with_gpt(text)
        else:
            summary = "본문 없음"

        summaries.append(summary)

    df['요약'] = summaries

    # 요약된 결과를 새로운 엑셀 파일로 저장
    df.to_excel(output_file, index=False)
    print(f"요약이 완료되었습니다. 결과는 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    date = '20250411'
    data_directory = "../data/"
    file_prefix = "건강"
    input_path = f"{data_directory}{file_prefix}_{date}_naver.xlsx"
    output_path = f"{data_directory}{file_prefix}_{date}_summary.xlsx"
    summarize_news_from_excel(input_path, output_path)
