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
# 1. 시스템 설정
# ==========================================
try:
    # Streamlit Secrets에서 API 키 로드
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = "YOUR_LOCAL_API_KEY_FOR_TEST"

# 모델명을 v1beta 버전에 맞는 전체 경로 형식으로 수정
MODEL_ID = "gemini-2.5-flash" 
client = genai.Client(api_key=API_KEY)

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
# 2. 유틸리티 및 분석 함수 (위치 중요)
# ==========================================
def get_week_of_month(dt):
    """날짜를 입력받아 해당 월의 몇째 주인지 반환합니다."""
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def analyze_pdf_document(file_path):
    temp_process_path = f"process_{int(time.time())}.pdf"
    try:
        shutil.copy2(file_path, temp_process_path)
        # PDF MimeType 명시
        with open(temp_process_path, "rb") as f:
            uploaded_doc = client.files.upload(
                file=f,
                config={'mime_type': 'application/pdf'}
            )
        
        prompt = f"""
        특허 마케팅 전문가로서 아래 PDF를 분석해 JSON으로만 응답하세요.
        항목: title(기술명), summary(3개 문장 리스트), category({TECH_CATEGORIES} 중 선택)
        형식: {{"title": "명칭", "summary": ["1", "2", "3"], "category": "분야"}}
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        
        try:
            client.files.delete(name=uploaded_doc.name)
        except:
            pass
            
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"분석 오류: {str(e)}")
        return {"title": "분석 지연", "summary": ["상세 내용은 SMK를 확인해주세요."], "category": "기타"}
    finally:
        if os.path.exists(temp_process_path):
            os.remove(temp_process_path)

def group_patents_by_category(patent_list):
    grouped = {}
    for cat in TECH_CATEGORIES:
        match = [p for p in patent_list if p.get("category") == cat]
        if match: grouped[cat] = match
    others = [p for p in patent_list if p.get("category") not in TECH_CATEGORIES]
    if others: grouped["기타"] = others
    return grouped

# [HTML 템플릿 코드는 기존과 동일하게 유지]
html_template_str = """... (기존 템플릿 코드 입력) ..."""

# ==========================================
# 3. Streamlit 웹 UI 실행부
# ==========================================
def main():
    st.set_page_config(page_title="PNUTH 뉴스레터 생성기", page_icon="🚀")
    if not os.path.exists("temp"):
        os.makedirs("temp")

    st.title("🚀 PNUTH 뉴스레터 자동 생성기")
    uploaded_files = st.file_uploader("SMK PDF 파일 업로드", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("뉴스레터 생성"):
            patent_list = []
            for uploaded_file in uploaded_files:
                file_path = os.path.join("temp", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                patent_id = uploaded_file.name.split('_')[0]
                data = analyze_pdf_document(file_path)
                data['patent_id'] = patent_id
                data['image_id'] = PATENT_IMAGE_IDS.get(patent_id, "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn")
                patent_list.append(data)
                time.sleep(1)

            grouped_patents = group_patents_by_category(patent_list)
            now = datetime.datetime.now()
            # 이제 NameError가 발생하지 않습니다.
            week_str = f"{now.year}년 {now.month}월 {get_week_of_month(now)}째주"
            
            template = Template(html_template_str)
            result_html = template.render(
                week_date=week_str,
                grouped_patents=grouped_patents,
                drive_url=GOOGLE_DRIVE_FOLDER_URL,
                logo_id=LOGO_IMAGE_ID,
                bldg_id=BUILDING_IMAGE_ID,
                consult_url=CONSULT_URL,
                pr_url=PR_URL
            )

            st.success("생성 완료!")
            st.download_button("HTML 다운로드", data=result_html, file_name=f"newsletter_{now.strftime('%Y%m%d')}.html")
            st.text_area("HTML 소스", value=result_html, height=300)

if __name__ == "__main__":
    main()
