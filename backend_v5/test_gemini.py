import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 키 로드
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 내 API 키로 사용 가능한 Gemini 모델 목록을 조회합니다...\n")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    print("\n✅ 조회 완료!")
except Exception as e:
    print(f"❌ 에러 발생: {e}")