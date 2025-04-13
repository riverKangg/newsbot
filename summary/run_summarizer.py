# run_summarizer.py

import pandas as pd
import sys
import asyncio
from summarizer import NewsSummarizer
from datetime import datetime
import json
import re

def parse_response(response):
    try:
        # 마크다운 코드 블록 제거
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1]
        if '```' in response:
            response = response.split('```')[0]
        response = response.strip()
            
        # JSON 파싱
        result = json.loads(response)
        
        # 필수 필드가 없는 경우 기본값 설정
        if 'is_related' not in result:
            result['is_related'] = False
        if 'label' not in result:
            result['label'] = 'False'
        if 'summary' not in result:
            result['summary'] = '요약 실패'
            
        # label 값이 예상된 형식이 아닌 경우 수정
        if isinstance(result['label'], bool):
            result['label'] = 'True' if result['label'] else 'False'
        elif result['label'] not in ['True', 'False', 'Positive', 'Negative', 'Neutral']:
            result['label'] = 'False'
            
        return result
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response}")
        return {
            'is_related': False,
            'label': 'False',
            'summary': '요약 실패'
        }

async def process_content_with_prompt(content, keywords, prompt):
    try:
        summarizer = NewsSummarizer()
        # 키워드를 프롬프트에 포함
        full_prompt = f"{prompt}\n\n관련 키워드: {keywords}"
        # GPT 호출을 asyncio.to_thread로 비동기 처리
        sentdict_raw = await asyncio.to_thread(summarizer.summarize_with_gpt, full_prompt, content)
        sentdict = parse_response(sentdict_raw)

        if sentdict is None:
            raise ValueError("GPT 응답을 파싱할 수 없습니다.")

        is_related = sentdict.get('is_related', False)
        label = sentdict.get('label')
        summary = sentdict.get('summary')

        if label is None or summary is None:
            raise ValueError("GPT 응답에 필수 필드가 없습니다.")

        return is_related, label, summary
    except Exception as e:
        print(f"Error in process_content_with_prompt: {str(e)}")
        print(f"Content: {content[:100]}...")  # 첫 100자만 로깅
        return None, None, None

async def summarize_news_from_excel(input_file, output_file, prompt, file_prefix):
    df = pd.read_excel(input_file)
    df  = df.drop_duplicates(subset='본문').reset_index(drop=True)
    labels, summarys, is_relateds = [None]*len(df), [None]*len(df), [None]*len(df)

    async def process_row(i, text, keywords, file_prefix):
        print(f"Processing article {i+1}/{len(df)}...")
        try:
            is_related, label, summary = await process_content_with_prompt(text, keywords, prompt)
            if is_related is None or label is None or summary is None:
                raise ValueError("GPT 응답이 올바르지 않습니다.")
            
            is_relateds[i] = is_related if file_prefix == "cnews" else None
            labels[i] = label
            summarys[i] = summary
        except Exception as e:
            print(f"Error processing row {i+1}: {str(e)}")
            is_relateds[i] = None
            labels[i] = "오류"
            summarys[i] = "요약 실패"

    tasks = []
    for i, row in df.iterrows():
        text = row['본문']
        keywords = row['키워드'] if '키워드' in row else ""
        if pd.notna(text):
            tasks.append(process_row(i, text, keywords, file_prefix))
        else:
            is_relateds[i] = None
            labels[i] = None
            summarys[i] = None 

        # 10개씩 실행 후 기다림
        if len(tasks) == 100:
            await asyncio.gather(*tasks)
            tasks = []

    if tasks:
        await asyncio.gather(*tasks)

    df['summary'] = summarys
    df['label'] = labels
    if file_prefix == "cnews":
        df['is_related'] = is_relateds
    df.to_excel(output_file, index=False)
    print(f"요약이 완료되었습니다. 결과는 {output_file}에 저장되었습니다.")

async def main():
    print("\n📄 사용법: python summarize_from_excel.py [health|cnews] [날짜: YYYYMMDD]")

    if len(sys.argv) != 3:
        print("\n❗ 인자 오류: 파일 접두사와 날짜를 정확히 입력해 주세요.")
        return

    file_prefix = sys.argv[1]
    date_str = sys.argv[2]

    print(f"\n🔍 처리 중인 파일 정보:")
    print(f" - 카테고리 : {file_prefix}")
    print(f" - 날짜     : {date_str}")

    try:
        with open(f"../prompt/{file_prefix}_summary.txt", 'r', encoding='utf-8') as file:
            prompt = file.read()
    except FileNotFoundError:
        print(f"\n🚫 프롬프트 파일을 찾을 수 없습니다: ../prompt/{file_prefix}_summary.py\n")
        return

    data_directory = "../data/"
    input_path = f"{data_directory}{file_prefix}_{date_str}_naver.xlsx"
    output_path = f"{data_directory}{file_prefix}_{date_str}_summary.xlsx"

    print(f"\n📂 입력 파일 경로 : {input_path}")
    print(f"📁 출력 파일 경로 : {output_path}\n")

    await summarize_news_from_excel(input_path, output_path, prompt, file_prefix)

    print("\n✅ 뉴스 요약 완료!\n")

if __name__ == "__main__":
    asyncio.run(main())
