import streamlit as st
import openai
import pandas as pd
import os
import json
from datetime import datetime

st.set_page_config(page_title="프롬프트 테스트", layout="wide")
st.title("📊 프롬프트 GPT 테스트")

openai.api_key = st.secrets["openai_api_key"]

# 디렉토리 경로
current_dir = os.path.dirname(__file__)
data_dir = os.path.abspath(os.path.join(current_dir, ".", "data"))
prompt_dir = os.path.abspath(os.path.join(current_dir, ".", "prompt"))
history_dir = os.path.abspath(os.path.join(current_dir, ".", "history"))
os.makedirs(history_dir, exist_ok=True)

# 📂 데이터 파일 선택
files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]
if not files:
    st.warning("data 폴더에 xlsx 파일이 없습니다.")
    st.stop()

selected_file = st.selectbox("엑셀 파일을 선택하세요", files)
df = pd.read_excel(os.path.join(data_dir, selected_file))
del_cols = ["링크","네이버링크","본문","기자링크", "선택","요약"]
df = df.drop(columns=del_cols, errors='ignore')
if "본문" in df.columns:
    df = df.dropna(subset=["본문"])
if "label" in df.columns:
    df = df.dropna(subset=["label"])

st.subheader("🔍 필터 설정")

# 선택 가능한 필터 컬럼 리스트 (선택 컬럼은 제외)
filterable_cols = [col for col in df.columns if col not in ["본문", "선택"]]
selected_filter_cols = st.multiselect("필터에 사용할 컬럼 선택", filterable_cols)

# 원본 복사
filter_df = df.copy()

# 선택된 컬럼에 따라 필터 위젯 생성
for col in selected_filter_cols:
    if pd.api.types.is_numeric_dtype(filter_df[col]):
        min_val, max_val = filter_df[col].min(), filter_df[col].max()
        selected_range = st.slider(f"{col} 범위", float(min_val), float(max_val), (float(min_val), float(max_val)))
        filter_df = filter_df[(filter_df[col] >= selected_range[0]) & (filter_df[col] <= selected_range[1])]
        
    elif pd.api.types.is_string_dtype(filter_df[col]) or pd.api.types.is_categorical_dtype(filter_df[col]):
        # NaN 포함된 임시 컬럼 생성
        temp_col = filter_df[col].fillna("❌ 없음")
        unique_vals = sorted(temp_col.unique())
        selected_vals = st.multiselect(f"{col} 필터", unique_vals)

        if selected_vals:
            # '❌ 없음' 포함 여부 확인
            include_nan = "❌ 없음" in selected_vals
            actual_selected_vals = [val for val in selected_vals if val != "❌ 없음"]

            # 원본 컬럼 기준으로 필터링
            condition = filter_df[col].isin(actual_selected_vals)
            if include_nan:
                condition = condition | filter_df[col].isna()
            filter_df = filter_df[condition]



# 필터링된 결과에 '선택' 체크박스 붙이기
filter_df["선택"] = False
filter_df = filter_df[["선택"] + [col for col in filter_df.columns if col != "선택"]]

select_all = st.checkbox("전체 선택", value=False)
if select_all:
    filter_df["선택"] = True

# ✅ 행 선택 UI
st.write("👇 사용하고 싶은 행에 체크해주세요")
edited_df = st.data_editor(
    filter_df,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="data_selector"
)
selected_rows_df = edited_df[edited_df["선택"] == True]


st.subheader("🔍 프롬프트에 넣을 컬럼 선택")

# 사용자가 선택할 컬럼 리스트 (선택 컬럼 제외)
columns_for_prompt = [col for col in df.columns if col != "선택"]
selected_columns = st.multiselect("프롬프트에 넣을 컬럼 선택", columns_for_prompt)

# 📦 선택한 행 데이터 문자열로 합치기
selected_data_str = ""
for i, row in selected_rows_df[selected_columns].iterrows():
    row_str = "\n".join([f"{k}: {v}" for k, v in row.astype(str).items()])
    selected_data_str += f"\n\n[Row {i}]\n{row_str}"
st.text_area("인풋 형태:\n", selected_data_str, height=200)


st.subheader("✍️  프롬프트 입력")
# 📁 프롬프트 템플릿 로딩
prompt_files = [f for f in os.listdir(prompt_dir) if f.endswith(".txt")]
selected_prompt_file = st.selectbox("프롬프트 템플릿 선택 (선택 안 해도 됨)", ["직접 입력"] + prompt_files)

default_prompt = ""
if selected_prompt_file != "직접 입력":
    with open(os.path.join(prompt_dir, selected_prompt_file), "r", encoding="utf-8") as f:
        default_prompt = f.read()

# ✍️ 프롬프트 입력
prompt = st.text_area("프롬프트를 입력하세요", value=default_prompt, height=350)
full_prompt = f"{prompt}\n\n선택된 데이터:\n{selected_data_str}"



# 💾 히스토리 저장 함수
def save_history(prompt_text, response_text):
    history_data = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt_text,
        "response": response_text,
    }
    filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(history_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

# 🤖 GPT 호출
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
                result = response.choices[0].message.content
                st.success("✅ GPT의 응답:")
                st.write(result)

                save_history(full_prompt, result)
                st.toast("히스토리에 저장되었습니다!", icon="💾")

            except Exception as e:
                st.error(f"에러 발생: {e}")

# 📜 히스토리 보기
with st.expander("📂 히스토리 보기"):
    hist_files = sorted(os.listdir(history_dir), reverse=True)
    if hist_files:
        selected_hist = st.selectbox("저장된 히스토리", hist_files)
        if selected_hist:
            with open(os.path.join(history_dir, selected_hist), "r", encoding="utf-8") as f:
                data = json.load(f)
                st.write("📝 **프롬프트:**")
                st.code(data["prompt"])
                st.write("🤖 **GPT 응답:**")
                st.code(data["response"])
    else:
        st.info("저장된 히스토리가 없습니다.")

