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

# 각 탭별 프롬프트와 데이터 파일 매핑
tab_configs = [
    {
        "name": "뉴스 요약",
        "prompt_file": "cnews_summary.txt",
        "data_file": "cnews_20250411_summary.xlsx",
        "description": "뉴스를 요약합니다.",
        "columns": ["키워드", "제목", "본문", "summary",  "label", "is_related"],
        "column_labels": {
            "summary": "기존요약결과",
            "label": "기존감정",
            "is_related": "기존관련기사여부"
        },
        "display_columns": ["키워드", "제목", "본문"],
        "max_rows": 1,
        "predefined_filters": {}
    },
    {
        "name": "부정적 뉴스 리포트",
        "prompt_file": "cnews_negative_report.txt",
        "data_file": "cnews_20250411_summary.xlsx",
        "description": "부정적인 뉴스를 분석하여 리포트를 생성합니다.",
        "columns": ["키워드", "제목", "본문", "언론사", "링크",  "label", "is_related"],
        "column_labels": {
            "label": "감정",
            "is_related": "관련 기사 여부"
        },
        "display_columns": ["키워드", "제목", "본문", "언론사", "링크"],
        "max_rows": 20,
        "predefined_filters": {
            "label": ["Negative"],
            "is_related": [True]
        }
    },
    {
        "name": "건강 뉴스 요약",
        "prompt_file": "health_summary.txt",
        "data_file": "health_20250411_summary.xlsx",
        "description": "건강 관련 뉴스를 요약합니다.",
        "columns": ["키워드", "제목", "본문", "summary","label"],
        "column_labels": {
            "summary": "기존요약결과",
            "label": "기존활용가능여부"
        },
        "display_columns": ["키워드", "제목", "본문"],
        "max_rows": 1,
        "predefined_filters": {
            "본문": lambda x: x is not None
        }
    },
    {
        "name": "건강 뉴스 TOP3",
        "prompt_file": "health_top3.txt",
        "data_file": "health_20250411_summary.xlsx",
        "description": "건강 관련 뉴스 중 가장 중요한 3개를 선정합니다.",
        "columns": ["키워드", "제목", "본문", "summary", "label"],
        "column_labels": {
            "summary": "요약",
            "label": "활용가능여부"
        },
        "display_columns": ["제목", "summary","label"],
        "max_rows": 10,
        "predefined_filters": {
            "label": [True]
        }
    },
    {
        "name": "건강 뉴스 리포트",
        "prompt_file": "health_report.txt",
        "data_file": "health_20250411_summary.xlsx",
        "description": "건강 관련 뉴스를 분석하여 리포트를 생성합니다.",
        "columns": ["키워드", "제목", "본문","label"],
        "column_labels": {
            "label": "활용가능여부"},
        "display_columns": ["키워드", "제목", "본문"],
        "max_rows": 3,
        "predefined_filters": {
            "label": [True]
        }
    },

]

# 탭 생성
tabs = st.tabs([config["name"] for config in tab_configs])

# 각 탭 생성
for i, config in enumerate(tab_configs):
    with tabs[i]:
        st.subheader(f"✍️ {config['name']}")
        st.write(f"**{config['description']}**")
        
        try:
            # 데이터 로드
            data_path = os.path.join(data_dir, config["data_file"])
            df = pd.read_excel(data_path)
            
            # 지정된 컬럼만 선택
            available_columns = [col for col in config["columns"] if col in df.columns]
            df = df[available_columns]
            
            # NaN 값이 있는 행 제거
            df = df.dropna()
            
            # 미리 정의된 필터 적용
            if config["predefined_filters"]:
                for col, condition in config["predefined_filters"].items():
                    if col in df.columns:
                        if isinstance(condition, list):
                            # Boolean 값 처리
                            if isinstance(condition[0], bool):
                                df = df[df[col] == condition[0]]
                            else:
                                df = df[df[col].isin(condition)]
                        elif callable(condition):
                            df = df[df[col].apply(condition)]
            
   
            # 프롬프트 로드
            prompt_path = os.path.join(prompt_dir, config["prompt_file"])
            with open(prompt_path, "r", encoding="utf-8") as f:
                default_prompt = f.read()
            
            # 데이터 선택 UI
            st.subheader("🔍 데이터 선택")
            
            # 필터 UI 추가
            st.subheader("필터 설정")
            filter_df = df.copy()
            
            # 필터에서 제외할 컬럼
            excluded_columns = ["본문", "제목", "summary", "링크", "is_related", "label","활용가능여부"]
            
            # 필터 가능한 컬럼 선택
            filterable_columns = [col for col in filter_df.columns if col not in excluded_columns]
            selected_filter_columns = st.multiselect(
                "필터에 사용할 컬럼 선택",
                filterable_columns,
                default=filterable_columns,
                key=f"filter_columns_{i}"
            )
            
            # 각 컬럼별 필터 생성
            for col in selected_filter_columns:
                if pd.api.types.is_numeric_dtype(filter_df[col]) and not pd.api.types.is_bool_dtype(filter_df[col]):
                    # 숫자형 컬럼의 경우 범위 슬라이더 (Boolean 제외)
                    min_val, max_val = filter_df[col].min(), filter_df[col].max()
                    # 최소값과 최대값이 같은 경우를 처리
                    if min_val == max_val:
                        max_val += 1  # 최대값에 1을 더해 차이를 만듦
                    selected_range = st.slider(
                        f"{col} 범위",
                        float(min_val),
                        float(max_val),
                        (float(min_val), float(max_val)),
                        key=f"filter_{col}_{i}"
                    )
                    filter_df = filter_df[
                        (filter_df[col] >= selected_range[0]) & 
                        (filter_df[col] <= selected_range[1])
                    ]
                else:
                    # 문자열/카테고리형/Boolean 컬럼의 경우 멀티셀렉트
                    unique_vals = sorted(filter_df[col].unique())
                    if pd.api.types.is_bool_dtype(filter_df[col]):
                        # Boolean 컬럼의 경우 True/False만 표시
                        unique_vals = [True, False]
                    selected_vals = st.multiselect(
                        f"{col} 필터",
                        unique_vals,
                        default=unique_vals,
                        key=f"filter_{col}_{i}"
                    )
                    if selected_vals:
                        filter_df = filter_df[filter_df[col].isin(selected_vals)]
            
            # '선택' 컬럼 추가
            filter_df["선택"] = False
            filter_df = filter_df[["선택"] + [col for col in filter_df.columns if col != "선택"]]
            
            # 선택 가능한 행 수 표시
            st.caption(f"선택 가능한 행 수: {config['max_rows']}개")
            
            # 데이터 에디터
            edited_df = st.data_editor(
                filter_df,
                use_container_width=True,
                num_rows="fixed",
                hide_index=True,
                key=f"data_editor_{i}",
                column_config={
                    "선택": st.column_config.CheckboxColumn(
                        "선택",
                        help="선택할 수 있는 최대 행 수: " + str(config["max_rows"]),
                        default=False,
                        width=50
                    ),
                    **{col: st.column_config.Column(
                        config["column_labels"].get(col, col),
                        help=config["column_labels"].get(col, col),
                        width=100
                    ) for col in filter_df.columns if col != "선택"}
                }
            )
            
            # 선택된 행만 필터링
            selected_df = edited_df[edited_df["선택"] == True]
            
            # 최대 선택 가능한 행 수 확인
            if len(selected_df) > config["max_rows"]:
                st.error(f"최대 {config['max_rows']}개의 행만 선택할 수 있습니다.")
                st.stop()
            
            if not selected_df.empty:
                # 선택된 데이터 표시
                st.subheader("✅ 선택된 데이터")
                
                # 컬럼 너비 설정
                column_config = {
                    col: st.column_config.Column(
                        config["column_labels"].get(col, col),
                        width="small"
                    ) for col in config["display_columns"]
                }
                
                # 데이터 에디터로 표시
                edited_df = st.data_editor(
                    selected_df[config["display_columns"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config,
                    disabled=True
                )
                
                # 📦 선택한 행 데이터 문자열로 합치기
                data_str = ""
                for idx, row in selected_df[config["display_columns"]].iterrows():
                    row_str = "\n".join([f"{k}: {v}" for k, v in row.astype(str).items()])
                    data_str += f"\n\n[Row {idx}]\n{row_str}"
                
                st.subheader("📝 전체 프롬프트")
                full_prompt = f"{default_prompt}\n\n데이터:\n{data_str}"
                edited_prompt = st.text_area("프롬프트를 수정하세요", value=full_prompt, height=300, key=f"full_prompt_{i}")
                
                # 🤖 GPT 호출 버튼
                if st.button("GPT에게 보내기", key=f"send_{i}"):
                    with st.spinner("GPT 응답을 기다리는 중..."):
                        try:
                            response = openai.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": "친절한 GPT 비서입니다."},
                                    {"role": "user", "content": edited_prompt},
                                ]
                            )
                            result = response.choices[0].message.content
                            st.success("✅ GPT의 응답:")
                            st.markdown(f'<div style="white-space: pre-wrap; word-wrap: break-word;">{result}</div>', unsafe_allow_html=True)

                            # 💾 히스토리 저장
                            history_data = {
                                "timestamp": datetime.now().isoformat(),
                                "prompt": edited_prompt,
                                "response": result,
                            }
                            filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            filepath = os.path.join(history_dir, filename)
                            with open(filepath, "w", encoding="utf-8") as f:
                                json.dump(history_data, f, ensure_ascii=False, indent=2)
                            st.toast("히스토리에 저장되었습니다!", icon="💾")

                        except Exception as e:
                            st.error(f"에러 발생: {e}")
            else:
                st.warning("데이터를 선택해주세요.")
                        
        except FileNotFoundError as e:
            st.error(f"파일을 찾을 수 없습니다: {e}")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

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

