import streamlit as st
import os
import time
import datetime
import json
import shutil
import math
from google import genai
from jinja2 import Template

# ==========================================
# 1. 시스템 설정 (Streamlit Secrets 활용)
# ==========================================
# 클라우드 배포 시 Settings -> Secrets에 등록한 키를 가져옵니다.
# 로컬 테스트 시에는 직접 문자열을 넣어도 되지만, 보안을 위해 secrets 권장합니다.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "여기에_직접_API키를_넣어_로컬테스트_가능"

MODEL_ID = "gemini-2.5-flash"
client = genai.Client(api_key=API_KEY)

# 기존 이미지 ID 및 URL 설정 (기존 코드와 동일)
LOGO_IMAGE_ID = "1WjzjlOOetztrcgq6rioAZxTzi_K-JwLl"
BUILDING_IMAGE_ID = "1f7XwQ2Z-43sECHQ53Of0J8NzqOeRh9Ll"
CONSULT_URL = "https://clever-designers-959477.framer.app/pium-%EA%B8%B0%EC%88%A0%EC%82%AC%EC%97%85%ED%99%94-%EC%84%BC%ED%84%B0-%EC%88%98%EC%9A%94%EA%B8%B0%EC%88%A0-%EC%A0%91%EC%88%98-%ED%8E%98%EC%9D%B4%EC%A7%80"
PR_URL = "https://link.inpock.co.kr/pnutlo?utm_source=ig&utm_medium=social&utm_content=link_in_bio"
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1bgCruhVa2AE_eH1OEq7lbZykQavFlw6S?hl=ko"

PATENT_IMAGE_IDS = {
    "10-2023-0143794": "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn",
    "10-2025-0105146": "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn",
    "10-2025-0108357": "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn",
    "10-2026-0061085": "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn",
}

TECH_CATEGORIES = ["바이오", "의료기기", "기계", "재료", "전기전자", "정보통신", "에너지자원", "원자력", "건설교통"]

# ==========================================
# 2. 유틸리티 및 분석 함수 (여기에 정의되어 있어야 합니다)
# ==========================================
def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def analyze_pdf_document(file_path):
    """PDF 분석 함수 로직"""
    temp_upload_path = "temp_process.pdf"
    categories_str = ", ".join(TECH_CATEGORIES)
    
    try:
        shutil.copy2(file_path, temp_upload_path)
        uploaded_doc = client.files.upload(file=temp_upload_path)
        
        prompt = f"""
        특허 마케팅 전문가로서 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.
        분석 항목:
        1. title: 기업 관점의 마케팅용 기술 명칭
        2. summary: 특장점 위주로 3개의 짧은 문장 리스트
        3. category: [{categories_str}] 중 선택
        응답 형식: {{"title": "기술명", "summary": ["문장1", "문장2", "문장3"], "category": "분야명"}}
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        client.files.delete(name=uploaded_doc.name)
        
        raw_text = response.text.strip()
        if "
http://googleusercontent.com/immersive_entry_chip/0

### 💡 확인 포인트
1.  **함수 정의 위치:** `analyze_pdf_document` 정의가 `main()` 함수보다 코드상 **위쪽**에 있어야 합니다.
2.  **전역 변수:** `API_KEY`나 `PATENT_IMAGE_IDS` 같은 변수들도 함수 밖 상단에 잘 정의되어 있는지 확인하세요.
3.  **들여쓰기:** `if __name__ == "__main__":` 은 반드시 맨 왼쪽 벽에 붙어 있어야 합니다.

파일을 저장하고 다시 실행하면 정상적으로 동작할 것입니다!

if __name__ == "__main__":
    main()
