import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📰 삼성생명 AI 뉴스룸")

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
    sizes = [positive_ratio, 1 - positive_ratio]
    colors = ['#4CAF50', '#F44336']
    fig = px.pie(
        names=["긍정", "부정"],
        values=sizes,
        color_discrete_sequence=colors,
        hole=0.5
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
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
    fig = px.line(
        x=list(range(1, 15)),
        y=[65, 60, 75, 76, 65, 55, 40, 85, 120, 110, 90, 95, 100, 130],
        markers=True,
        labels={"x": "날짜", "y": "기사 수"}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**주요 키워드**")
    keywords = {"보험": 50, "디지털": 30, "서비스": 40, "소비자": 25, "시장": 35}

    # 키워드 데이터를 데이터프레임으로 변환
    df_keywords = pd.DataFrame(list(keywords.items()), columns=["키워드", "빈도"])

    # 트리맵 차트를 생성
    fig = px.treemap(
        df_keywords,
        path=['키워드'],
        values='빈도',
        color='빈도',
        color_continuous_scale='Blues'
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("🕒 실시간 기사")

# 데이터프레임 설정
df = pd.DataFrame([
    {"시간": "14:23", "매체": "경제일보", "기자": "김기자", "제목": "신규 친환경 기술 개발로 시장선도", "감성": "긍정", "링크": "https://example.com/1"},
    {"시간": "13:45", "매체": "금융투데이", "기자": "이기자", "제목": "분기별 실적 발표, 예상치 상회", "감성": "긍정", "링크": "https://example.com/2"},
    {"시간": "12:30", "매체": "IT뉴스", "기자": "박기자", "제목": "신제품 출시 행사에서 큰 호응","감성": "긍정", "링크": "https://example.com/3"},
])

# 링크 클릭 가능하게 하는 함수
def make_clickable(link):
    return f'<a href="{link}" target="_blank">🔗</a>'

# 링크를 HTML로 담아서 표시하는 대신, 직접 렌더러로 감성이나 링크를 처리한다.
df["감성"] = df["감성"].apply(lambda x: f"✔️ {x}" if x == "긍정" else f"❌ {x}")

grid_options = GridOptionsBuilder.from_dataframe(df)
grid_options.configure_column("링크", renderer="func", valueGetter="data.링크")
grid_options.configure_pagination(enabled=True)
grid_options.configure_default_column(resizable=True)
grid_options = grid_options.build()


# AgGrid를 사용하여 데이터프레임 출력
AgGrid(df, gridOptions=grid_options, height=300, fit_columns_on_grid_load=True)

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
    fig = px.bar(
        x=list(media_counts.keys()),
        y=list(media_counts.values()),
        labels={'x': '매체', 'y': '기사 수'},
        # color=list(media_counts.keys()),  # 매체별로 색상을 다르게
        color_discrete_sequence=px.colors.qualitative.Pastel  # 좀 더 부드러운 색상 사용
    )
    fig.update_layout(xaxis_title="매체", yaxis_title="기사 수", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)

# 📋 오른쪽: 기자별 기사 수 (Table 스타일)
with col2:
    st.markdown("**기자별 기사 수**")
    reporter_df = pd.DataFrame(list(reporter_counts.items()), columns=["기자", "기사 수"])
    reporter_df.index = reporter_df.index + 1  # 번호를 1부터 시작
    st.dataframe(reporter_df, use_container_width=True)
