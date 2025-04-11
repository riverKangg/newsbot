import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📰 뉴스 모니터링 대시보드")

plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# 상단 검색 영역
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.selectbox("날짜", ["오늘", "어제", "이번 주", "이번 달"])
with col2:
    st.text_input("키워드를 입력해 주세요")
with col3:
    st.button("🔍 검색")

st.markdown("---")

# 상단 요약 영역 (파이 차트들)
st.subheader("뉴스 분류")
col1, col2, col3, col4 = st.columns(4)

def pie_chart(label, positive_ratio=0.7):
    fig, ax = plt.subplots()
    sizes = [positive_ratio, 1 - positive_ratio]
    colors = ['#4CAF50', '#F44336']
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops={'width':0.5})
    ax.axis('equal')
    st.pyplot(fig)
    st.markdown(f"**{label}**")
    st.markdown("🔴 부정 뉴스 예: ~~서비스 장애로 고객 불만~~")

with col1:
    pie_chart("당사 관련 뉴스", 0.65)
with col2:
    pie_chart("보험업계 뉴스", 0.7)
with col3:
    pie_chart("관계사 뉴스", 0.75)
with col4:
    pie_chart("금융업계 뉴스", 0.8)

st.markdown("---")

# 주요 뉴스 카드
st.subheader("오늘의 주요 뉴스")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("경제일보 | 😊 긍정")
    st.markdown("**신규 디지털 금융 서비스 출시로 고객 편의성 향상**")
    st.write("당사가 개발한 디지털 금융 서비스가 큰 호응을 얻고 있습니다.")
    st.button("기사 보기", key="card1")
with col2:
    st.caption("지속가능경제 | 😊 긍정")
    st.markdown("**ESG 경영 실천으로 지속가능경영 선도**")
    st.write("당사의 ESG 경영 실천이 업계의 모범사례로 주목받고 있습니다.")
    st.button("기사 보기", key="card2")
with col3:
    st.caption("보험경제 | 😊 긍정")
    st.markdown("**혁신적인 보험 상품 출시로 시장 경쟁력 강화**")
    st.write("보험업계에서 혁신적인 상품 출시가 이어지고 있습니다.")
    st.button("기사 보기", key="card3")

st.markdown("---")

# 기사 수 추이 + 워드 클라우드
st.subheader("📊 기사 트렌드")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**기사 수 추이**")
    fig, ax = plt.subplots()
    x = list(range(1, 15))
    y = [65, 60, 75, 76, 65, 55, 40, 85, 120, 110, 90, 95, 100, 130]
    ax.plot(x, y, marker='o')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}일" for i in x])
    st.pyplot(fig)

with col2:
    st.markdown("**주요 키워드**")
    keywords = {"보험": 50, "디지털": 30, "서비스": 40, "소비자": 25, "시장": 35}
    wordcloud = WordCloud(width=400, height=250, background_color="white", font_path="/System/Library/Fonts/AppleGothic.ttf").generate_from_frequencies(keywords)
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

st.markdown("---")

# 실시간 기사 테이블
st.subheader("🕒 실시간 기사")
df = pd.DataFrame([
    {"시간": "14:23", "매체": "경제일보", "기자": "김기자", "제목": "신규 친환경 기술 개발로 시장 선도", "감성": "긍정", "링크": "https://example.com/1"},
    {"시간": "13:45", "매체": "금융투데이", "기자": "이기자", "제목": "분기별 실적 발표, 예상치 상회", "감성": "긍정", "링크": "https://example.com/2"},
    {"시간": "12:30", "매체": "IT뉴스", "기자": "박기자", "제목": "신제품 출시 행사에서 큰 호응", "감성": "긍정", "링크": "https://example.com/3"},
])

def make_clickable(link):
    return f'<a href="{link}" target="_blank">🔗</a>'

df["링크"] = df["링크"].apply(make_clickable)
df["감성"] = df["감성"].apply(lambda x: f'<span style="color: green; background: #d1fae5; padding: 3px 6px; border-radius: 8px;">{x}</span>')
st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.subheader("📈 매체/기자 통계")

# 데이터 정의
media_counts = {
    "경제일보": 34,
    "금융투데이": 28,
    "IT뉴스": 22,
    "산업경제": 18,
    "동반성장신문": 13
}

reporter_counts = {
    "김기자": 12,
    "이기자": 10,
    "박기자": 8,
    "최기자": 7,
    "정기자": 5,
    "신기자": 4
}

# 레이아웃 분리
col1, col2 = st.columns(2)

# 📊 왼쪽: 매체별 기사 수 (Bar chart)
with col1:
    st.markdown("**매체별 기사 수**")
    fig, ax = plt.subplots()
    ax.bar(media_counts.keys(), media_counts.values(), color='#1f77b4')
    ax.set_ylabel("기사 수")
    ax.set_xticklabels(media_counts.keys(), rotation=15)
    st.pyplot(fig)

# 📋 오른쪽: 기자별 기사 수 (Table 스타일)
with col2:
    st.markdown("**기자별 기사 수**")
    reporter_df = pd.DataFrame(list(reporter_counts.items()), columns=["기자", "기사 수"])
    reporter_df.index = reporter_df.index + 1  # 번호를 1부터 시작
    st.dataframe(reporter_df, use_container_width=True)
