import pandas as pd
import json
import argparse

def convert_excel_to_json(input_path: str, output_path: str):
    # 엑셀 파일 읽기
    df = pd.read_excel(input_path)

    if 'sentiment' in df.columns:
        df['sentiment'] = df['sentiment'].apply(lambda x: f"{x} as const")

    # 딕셔너리 리스트로 변환
    data = df.to_dict(orient='records')

    # JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON 파일이 저장되었습니다: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="엑셀을 JSON 형식으로 변환합니다.")
    parser.add_argument("--input", "-i", required=True, help="입력 엑셀 파일 경로")
    parser.add_argument("--output", "-o", default="news_data.json", help="출력 JSON 파일 경로")
    
    args = parser.parse_args()
    convert_excel_to_json(args.input, args.output)

