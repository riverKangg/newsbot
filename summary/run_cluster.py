import os
import sys
import time
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from tqdm import tqdm
from dotenv import load_dotenv
from openai import AsyncOpenAI

client = None  # 글로벌 AsyncOpenAI 클라이언트

def load_api_key():
    global client
    load_dotenv('../.env')
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY가 .env에서 로드되지 않았어요!")
    client = AsyncOpenAI(api_key=api_key)

def load_data(file_path, max_chars=800):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=["label"]).reset_index(drop=True)
    #df["text"] = df["제목"].fillna("") + " " + df["본문"].apply(lambda x: x[:max_chars]).fillna("")
    def get_text(row):
        if row["label"] in [True, "Negative"]:
            title = row["제목"] if pd.notna(row["제목"]) else ""
            content = row["본문"][:max_chars] if pd.notna(row["본문"]) else ""
            return title + " " + content
        return None

    df["text"] = df.apply(get_text, axis=1)
    return df

async def async_get_embedding(text, model="text-embedding-3-small", retry=3):
    if text is None:
        return [0.0] * 1536  # 만약 text가 None이라면 실패 시 zero vector 반환

    text = text.replace("\n", " ")
    for _ in range(retry):
        try:
            response = await client.embeddings.create(
                input=[text],
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Embedding error: {e}")
            await asyncio.sleep(2)
    return [0.0] * 1536  # 실패 시 zero vector

async def embed_all_async(df, batch_size=100):
    print("▶ 임베딩 생성 중 (비동기)...")
    texts = df["text"].tolist()
    embeddings = []

    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        tasks = [async_get_embedding(text) for text in batch]
        results = await asyncio.gather(*tasks)
        embeddings.extend(results)

    df["embedding"] = embeddings
    return df

def cluster_articles(df, eps=0.3, min_samples=2):
    print("▶ 유사도 계산 및 클러스터링 중...")
    X = np.array(df["embedding"].tolist())
    sim_matrix = cosine_similarity(X)

    # 거리 행렬로 변환 (음수 방지)
    distance_matrix = 1 - sim_matrix
    distance_matrix = np.clip(distance_matrix, 0, 1)

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = clustering.fit_predict(distance_matrix)
    df["cluster"] = labels
    return df

def select_representative(group):
    priority = ["조선일보", "중앙일보", "동아일보", "서울경제", "한국경제", "매일경제"]
    
    # 1. 제목에 "단독" 포함된 기사 있으면 그 중 첫 번째
    exclusive = group[group["제목"].str.contains("단독", na=False)]
    if not exclusive.empty:
        return exclusive.iloc[0]

    # 2. 우선순위 언론사 필터
    for media in priority:
        selected = group[group["언론사"] == media]
        if not selected.empty:
            return selected.iloc[0]

    # 3. 그래도 없으면 그냥 첫 번째
    return group.iloc[0]

def force_cluster_for_exclusives(df):
    exclusive_mask = df["제목"].str.contains("단독", na=False)
    noise_mask = df["cluster"] == -1
    exclusive_noise_idx = df[exclusive_mask & noise_mask].index

    # 새로운 cluster 번호를 가장 큰 클러스터 번호 다음부터 부여
    max_cluster = df["cluster"].max()
    for i, idx in enumerate(exclusive_noise_idx):
        df.at[idx, "cluster"] = max_cluster + 1 + i

    return df


def extract_representatives(df):
    print("▶ 대표 기사 선택 중...")
    representatives = []
    for label in set(df["cluster"]):
        group = df[df["cluster"] == label]
        if label == -1:
            representatives.append(group)  # noise는 전부 포함
        else:
            rep = select_representative(group)
            representatives.append(pd.DataFrame([rep]))
    return pd.concat(representatives, ignore_index=True)

def save_results(df, output_path="대표기사_결과_openai.xlsx"):
    df.to_excel(output_path, index=False)
    print(f"✅ 완료! 결과 저장됨: {output_path}")

def main():
    print("\n📄 사용법: python run_cluster.py [health|cnews] [날짜: YYYYMMDD]")

    if len(sys.argv) != 3:
        print("\n❗ 인자 오류: 파일 접두사와 날짜를 >정확히 입력해 주세요.")
        return

    file_prefix = sys.argv[1]
    date_str = sys.argv[2]

    print(f"\n🔍 처리 중인 파일 정보:")
    print(f" - 카테고리 : {file_prefix}")
    print(f" - 날짜     : {date_str}")

    data_directory = "../data/"

    input_path = f"{data_directory}{file_prefix}_{date_str}_summary.xlsx"
    output_path = f"{data_directory}{file_prefix}_{date_str}_cluster.xlsx"

    load_api_key()
    df = load_data(input_path)
    df = asyncio.run(embed_all_async(df))  # async 처리!
    df = cluster_articles(df)
    df = force_cluster_for_exclusives(df)
    result_df = extract_representatives(df)
    save_results(result_df, output_path)

if __name__ == "__main__":
    main()

