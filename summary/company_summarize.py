# company_summarize.py 
import pandas as pd
import sys
import asyncio
from summarizer import NewsSummarizer
from datetime import datetime
import json
import re

def parse_response(response):
    try:
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            print("No JSON found in the response.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

async def process_content_with_prompt(content, prompt):
    try:
        summarizer = NewsSummarizer()
        # GPT 호출을 asyncio.to_thread로 비동기 처리
        sentdict_raw = await asyncio.to_thread(summarizer.summarize_with_gpt, content, prompt)
        sentdict = parse_response(sentdict_raw)

        if sentdict is None:
            raise ValueError("Parsed dictionary is None.")

        sentiment_label = sentdict.get('sentiment')
        neg_sent = sentdict.get('sentence')

        if not sentiment_label or not neg_sent:
            raise ValueError("Sentiment or sentence is missing.")
    except Exception as e:
        print(f"Error processing content: {e}")
        return None, None

    return sentiment_label, neg_sent

async def summarize_news_from_excel(input_file, output_file, prompt):
    df = pd.read_excel(input_file)
    sentiments, sentences = [None]*len(df), [None]*len(df)

    async def process_row(i, text):
        print(f"Processing article {i+1}/{len(df)}...")
        sentiment, sentence = await process_content_with_prompt(text, prompt)
        sentiments[i] = sentiment or "오류"
        sentences[i] = sentence or "오류"

    tasks = []
    for i, row in df.iterrows():
        text = row['본문']
        if pd.notna(text):
            tasks.append(process_row(i, text))
        else:
            sentiments[i] = None
            sentences[i] = None 

        # 10개씩 실행 후 기다림
        if len(tasks) == 100:
            await asyncio.gather(*tasks)
            tasks = []

    if tasks:
        await asyncio.gather(*tasks)

    df['summary'] = sentences
    df['sentiment'] = sentiments
    df.to_excel(output_file, index=False)
    print(f"요약이 완료되었습니다. 결과는 {output_file}에 저장되었습니다.")

async def main():
    print("사용법: python summarize_from_excel.py [날짜YYYYMMDD]")
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y%m%d")
    print(date_str)

    file_prefix = "회사"
    prompt = """
너는 삼성생명 홍보팀 직원이야.
기사에 대한 긍부정을 판단하고,
회사에 보고할 수 있게 기사를 한 줄로 정리해줘.

1. Classify the sentiment as one of the following: Positive, Negative, or Neutral.
2. 회사에 보고할 수 있게 한 문장으로 작성해줘. 한글로 작성해.
3. Return the result in a strict JSON format using the keys: 'sentiment' and 'sentence'.

Expected return format:
{
    "sentiment": "Positive" | "Negative" | "Neutral",
    "sentence": "One-sentence summary that reflects the sentiment."
}
""" 
    data_directory = "../data/"
    input_path = f"{data_directory}{file_prefix}_{date_str}_naver.xlsx"
    output_path = f"{data_directory}{file_prefix}_{date_str}_summary.xlsx"

    await summarize_news_from_excel(input_path, output_path, prompt)

if __name__ == "__main__":
    asyncio.run(main())

