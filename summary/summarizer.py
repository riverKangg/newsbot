# summary/summarizer.py
import os
import openai
import sys
from dotenv import load_dotenv

load_dotenv()

class NewsSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def summarize_with_gpt(self, user_message, text):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                    {"role": "user", "content": f"{user_message}: {text}"}
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

def read_prompt_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
    except Exception as e:
        print(f"파일을 읽는 중 오류 발생: {e}")

    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python summarizer.py [사용자메시지] [파일경로]")
        sys.exit(1)

    user_message = sys.argv[1]
    input_file = sys.argv[2]

    prompt_text = read_prompt_from_file(input_file)
    if prompt_text:
        summarizer = NewsSummarizer()
        summary = summarizer.summarize_with_gpt(user_message, prompt_text)
        print("요약 결과:", summary)
