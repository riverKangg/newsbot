# summary/summarizer.py

import os
import openai
from dotenv import load_dotenv

load_dotenv()

class NewsSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def summarize_with_gpt(self, text):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                    {"role": "user", "content": f"다음 기사의 내용을 한줄로 요약해줘. 한글로 작성해야해.: {text}"}
                ],
                max_tokens=500,
                n=1,
                stop=None,
                temperature=0.5,
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print("GPT 요약 오류:", e)
            return "요약 실패"

if __name__ == "__main__":
    # 테스트 코드
    summarizer = NewsSummarizer()
    test_text = "President Joe Biden met with Ukrainian leaders in Warsaw to discuss the ongoing conflict, emphasizing the United States' continued support for Ukraine."
    print(summarizer.summarize_with_gpt(test_text))
