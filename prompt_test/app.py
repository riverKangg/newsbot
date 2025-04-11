import streamlit as st
import openai
import pandas as pd
import os

st.title("프롬프트 테스트")

openai.api_key = st.secrets["openai_api_key"]

# 1. 엑셀 파일 선택
current_dir = os.path.dirname(__file__)  # app.py 가 있는 폴더
data_dir = os.path.abspath(os.path.join(current_dir, ".", "data"))
files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]

if not files:
    st.warning("`/data` 폴더에 .xlsx 파일이 없습니다.")
else:
    selected_file = st.selectbox("엑셀 파일을 선택하세요", files)
    df = pd.read_excel(os.path.join(data_dir, selected_file))

    # 2. 선택용 체크박스 열 추가
    st.write("✅ 사용하고 싶은 행에 체크해주세요")
    df["선택"] = False
    df = df[["선택"] + [col for col in df.columns if col != "선택"]]

    # ✅ 전체 선택 체크박스
    select_all = st.checkbox("전체 선택")

    if select_all:
        df["선택"] = True

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key="data_selector"
    )

    # 3. 선택된 행 필터링
    selected_rows_df = edited_df[edited_df["선택"] == True]

    # 4. 프롬프트 입력
    prompt = st.text_area("프롬프트를 입력하세요", placeholder="예: 아래 데이터를 요약해줘", height=150)

    # 5. 전체 프롬프트 구성
    selected_data_str = ""
    for i, row in selected_rows_df.drop(columns=["선택"]).iterrows():
        row_str = "\n".join([f"{k}: {v}" for k, v in row.astype(str).items()])
        selected_data_str += f"\n\n[Row {i}]\n{row_str}"

    full_prompt = f"{prompt}\n\n선택된 데이터:\n{selected_data_str}"

    # 6. GPT 호출
    if st.button("GPT에게 보내기"):
        if not prompt:
            st.error("프롬프트를 입력해주세요.")
        elif selected_rows_df.empty:
            st.error("최소 한 개 이상의 행을 선택해주세요.")
        else:
            with st.spinner("GPT 응답을 기다리는 중..."):
                try:
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "친절한 GPT 비서입니다."},
                            {"role": "user", "content": full_prompt},
                        ]
                    )
                    st.success("GPT의 응답:")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"에러 발생: {e}")

