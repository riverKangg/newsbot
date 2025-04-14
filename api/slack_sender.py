# slack_sender.py
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

def send_slack_message(channel, message):
    """
    슬랙 채널에 메시지를 보냅니다.

    Args:
    channel (str): 메시지를 보낼 슬랙 채널의 이름 혹은 ID.
    message (str): 보낼 메시지 내용.

    Returns:
    None
    """
    client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
    try:
        response = client.chat_postMessage(channel=channel, text=message)
        print(f"메시지가 성공적으로 전송되었습니다: {response['message']['ts']}")
    except SlackApiError as e:
        print(f"슬랙 API에 오류가 발생했습니다: {e.response['error']}")

def create_message(news):
    if news['jour_name'] is not None and news['phone_number'] is None :
        message = f"""
🚨 [부정기사 감지]
키워드: {news['keyword']}
제목: {news['title']}
언론사: {news['press']}
기자: {news['jour_name']}
기자연락처: {news['phone_number']}
링크: {news['url']}
요약: {news['neg_sent']}

"""
    elif news['phone_number'] is None:
        message = f"""
🚨 [부정기사 감지]
키워드: {news['keyword']}
제목: {news['title']}
언론사: {news['press']}
기자: {news['jour_name']}
링크: {news['url']}
요약: {news['neg_sent']}

"""
    else:
        message = f"""
🚨 [부정기사 감지]
키워드: {news['keyword']}
제목: {news['title']}
언론사: {news['press']}
링크: {news['url']}
요약: {news['neg_sent']}

"""
    return message

def format_news_to_message(news):
    """
    뉴스 데이터에서 슬랙 메시지 형식으로 변환합니다.

    Args:
    news_data (list of dicts): 뉴스 항목 목록, 각 항목은 제목, 요약 등을 포함합니다.

    Returns:
    str: 슬랙에서 보낼 전체 메시지 텍스트.
    """
    return create_message(news)

# 테스트용 main 함수 호추가
def main():
    # 테스트용 뉴스 데이터
    test_news_data = [
        {"제목": "파이썬 슈퍼 파워", "요약": "파이썬이 대단한 이유에 대해서 설명해줘요.", "링크":
"https://example.com"},
        {"제목": "AI의 미래", "요약": "인공 지능이 우리 삶에 미치는 영향에 대해 알아봅니다.",
"링크": "https://example.com"}
    ]
    message = format_news_to_message(test_news_data)
    send_slack_message("#newsbot-test", message)

if __name__ == "__main__":
    main()
