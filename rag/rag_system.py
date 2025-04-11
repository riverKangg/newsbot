# rag_system.py

import os
import pandas as pd
from dotenv import load_dotenv

# from langchain.embeddings import OpenAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema.document import Document

# 🔐 .env 파일에서 API 키 로드
load_dotenv(dotenv_path='../../.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 📄 1. 엑셀 문서 로딩
df = pd.read_excel("../data/건강_20250411_summary.xlsx")

# 🧩 2. Document 객체 생성
documents = []
for _, row in df.iterrows():
    if pd.notna(row["본문"]):
        content = str(row["본문"])
        metadata = {
            "제목": row["제목"],
            "언론사": row["언론사"],
            "요약": row["요약"],
            "링크": row["링크"],
            "분류": row["분류"],
            "키워드": row["키워드"]
        }
        documents.append(Document(page_content=content, metadata=metadata))

# ✂️ 3. 텍스트 분할
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
split_docs = text_splitter.split_documents(documents)

# 🤖 4. 임베딩 생성
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")

# 💾 5. Chroma 벡터 저장소에 저장
vectordb = Chroma.from_documents(split_docs, embedding_model, persist_directory="./chroma_db")

# 💬 6. QA 체인 구성
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o")

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectordb.as_retriever(),
    chain_type="map_reduce",  # 간단하게 모든 문서 붙여서 전달
    return_source_documents=True
)

# 🚀 7. 테스트 실행
if __name__ == "__main__":
    while True:
        query = input("\n🧠 질문을 입력하세요 (종료하려면 'exit') >> ")
        if query.lower() == "exit":
            break

        result = qa_chain(query)
        print("\n📌 답변:\n", result["result"])
        print("\n🔗 참고 문서:")
        for doc in result["source_documents"]:
            meta = doc.metadata
            print(f"- {meta.get('제목')} ({meta.get('링크')})")

