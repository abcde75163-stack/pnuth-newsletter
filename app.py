import streamlit as st
import os
import time
import datetime
import json
import shutil
import math
import base64
from google import genai
from jinja2 import Template

# ==========================================
# 1. 시스템 설정
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "YOUR_LOCAL_API_KEY"

# 모델 ID 설정 (2.0-flash가 현재 가장 안정적입니다)
MODEL_ID = "gemini-2.0-flash" 
client = genai.Client(api_key=API_KEY)

# 기본 설정 (부산대 기술지주 전용)
LOGO_IMAGE_ID = "1WjzjlOOetztrcgq6rioAZxTzi_K-JwLl"
BUILDING_IMAGE_ID = "1f7XwQ2Z-43sECHQ53Of0J8NzqOeRh9Ll"
CONSULT_URL = "https://clever-designers-959477.framer.app/pium-%EA%B8%B0%EC%88%A0%EC%82%AC%EC%97%85%ED%99%94-%EC%84%BC%ED%84%B0-%EC%88%98%EC%9A%94%EA%B8%B0%EC%88%A0-%EC%A0%91%EC%88%98-%ED%8E%98%EC%9D%B4%EC%A7%80"
PR_URL = "https://link.inpock.co.kr/pnutlo?utm_source=ig&utm_medium=social&utm_content=link_in_bio"
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1bgCruhVa2AE_eH1OEq7lbZykQavFlw6S?hl=ko"

TECH_CATEGORIES = ["바이오", "의료기기", "기계", "재료", "전기전자", "정보통신", "에너지자원", "원자력", "건설교통"]

# ==========================================
# 2. 핵심 로직 함수
# ==========================================
def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def analyze_pdf_document(file_obj):
    """UploadedFile 객체를 받아 분석을 수행합니다."""
    temp_path = f"temp_{int(time.time())}.pdf"
    try:
        # 1. 파일 임시 저장 (TypeError 방지)
        with open(temp_path, "wb") as f:
            f.write(file_obj.getbuffer())
        
        # 2. 업로드 및 분석
        with open(temp_path, "rb") as f:
            uploaded_doc = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
        
        prompt = f"""
        특허 마케팅 전문가로서 아래 PDF를 분석하여 JSON 형식으로만 응답하세요.
        항목: title(기술명), summary(3개 문장 리스트), category({TECH_CATEGORIES} 중 선택)
        형식: {{"title": "명칭", "summary": ["1", "2", "3"], "category": "분야"}}
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        
        try: client.files.delete(name=uploaded_doc.name)
        except: pass
            
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        return {"title": "분석 지연", "summary": [f"상세 내용은 SMK를 확인해주세요.", f"사유: {str(e)[:30]}"], "category": "기타"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

def group_patents_by_category(patent_list):
    grouped = {}
    for cat in TECH_CATEGORIES + ["기타"]:
        match = [p for p in patent_list if p.get("category") == cat]
        if match: grouped[cat] = match
    return grouped

# ==========================================
# 3. Streamlit 웹 UI
# ==========================================
def main():
    st.set_page_config(page_title="PNUTH 뉴스레터 생성기", page_icon="🚀")
    if not os.path.exists("temp"): os.makedirs("temp")

    st.title("🚀 PNUTH 뉴스레터 생성기 (통합 버전)")
    st.info("PDF와 이미지 파일을 함께 업로드하세요.") # 문법 오류 수정 완료

    # 파일 업로드 섹션
    col1, col2 = st.columns(2)
    with col1:
        pdf_files = st.file_uploader("1. SMK PDF 파일들", type="pdf", accept_multiple_files=True)
    with col2:
        img_files = st.file_uploader("2. 특허 이미지들 (번호 일치)", type=["png", "jpg"], accept_multiple_files=True)

    if pdf_files:
        if st.button("뉴스레터 생성 시작"):
            # 이미지 매핑 준비
            image_map = {os.path.splitext(img.name)[0]: img for img in img_files}
            
            patent_list = []
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(pdf_files):
                patent_id = uploaded_file.name.split('_')[0]
                status_text.text(f"⏳ {patent_id} 분석 중... ({idx+1}/{len(pdf_files)})")
                
                # 분석 실행
                data = analyze_pdf_document(uploaded_file)
                data['patent_id'] = patent_id
                
                # 이미지 처리 (여기서는 임시로 구글 드라이브 ID 체계 유지 혹은 URL 로직 삽입)
                data['image_id'] = "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn" # 기본값
                
                patent_list.append(data)
                progress_bar.progress((idx + 1) / len(pdf_files))
                time.sleep(1)

            # HTML 생성 및 다운로드 (이하 기존 로직과 동일)
            status_text.success("🎉 분석 완료!")
            # 모든 분석이 끝난 후 실행되는 구간입니다.
            status_text.success("🎉 모든 기술 분석이 완료되었습니다!")
            progress_bar.empty() # 진행바 제거

            if patent_list:
                # 1. 카테고리별 그룹화
                grouped_patents = group_patents_by_category(patent_list)
                
                # 2. 날짜 정보 생성
                now = datetime.datetime.now()
                week_str = f"{now.year}년 {now.month}월 {get_week_of_month(now)}째주"
                
                # 3. HTML 템플릿 렌더링
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

                # 4. 화면에 결과물 표시 및 다운로드 버튼 생성
                st.divider()
                st.subheader("📄 생성된 뉴스레터 미리보기")
                
                # HTML 다운로드 버튼 (이 버튼이 있어야 파일 저장이 가능합니다)
                st.download_button(
                    label="📂 뉴스레터 HTML 파일 다운로드",
                    data=result_html,
                    file_name=f"PNUTH_Newsletter_{now.strftime('%Y%m%d')}.html",
                    mime="text/html",
                    help="클릭하면 완성된 뉴스레터 파일을 내 컴퓨터에 저장합니다."
                )

                # 복사/붙여넣기용 소스 코드 영역
                with st.expander("🔗 HTML 소스 코드 복사 (메일 발송용)"):
                    st.code(result_html, language="html")
                    st.info("위 코드를 복사하여 메일 작성기의 'HTML 편집' 모드에 붙여넣으세요.")
                
                # 실제 화면에 미리보기 출력
                st.components.v1.html(result_html, height=800, scrolling=True)
            else:
                st.warning("분석된 특허 데이터가 없습니다. PDF 파일을 다시 확인해 주세요.")

if __name__ == "__main__":
    main()
