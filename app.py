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
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = "여기에_직접_API키를_넣어_로컬테스트_가능"

# 모델명을 가장 안정적인 1.5-flash로 설정합니다.
MODEL_ID = "gemini-1.5-flash"
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
# 2. 유틸리티 및 분석 함수
# ==========================================
def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def analyze_pdf_document(file_path):
    # 각 파일 분석 시 고유한 임시 파일명 사용
    temp_process_path = f"process_{int(time.time())}.pdf"
    
    try:
        shutil.copy2(file_path, temp_process_path)
        # 클라우드 환경에서는 path 인자를 명시적으로 사용합니다.
        uploaded_doc = client.files.upload(path=temp_process_path)
        
        prompt = f"""
        특허 마케팅 전문가로서 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.
        분석 항목:
        1. title: 기업 관점의 마케팅용 기술 명칭
        2. summary: 특장점 위주로 3개의 짧은 문장 리스트
        3. category: {TECH_CATEGORIES} 중 가장 적합한 하나 선택
        응답 형식: {{"title": "기술명", "summary": ["문장1", "문장2", "문장3"], "category": "분야명"}}
        """
        
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        client.files.delete(name=uploaded_doc.name)
        
        raw_text = response.text.strip()
        # JSON 블록 추출 로직
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_text)
        
    except Exception as e:
        # 분석 실패 시 에러 정보를 포함하여 반환
        return {
            "title": "기술 분석 진행 중",
            "summary": ["상세 내용은 하단 SMK 전체보기를 활용해 주세요.", f"사유: {str(e)[:30]}"],
            "category": "기타"
        }
    finally:
        if os.path.exists(temp_process_path):
            os.remove(temp_process_path)

def group_patents_by_category(patent_list):
    grouped = {}
    for cat in TECH_CATEGORIES:
        match = [p for p in patent_list if p.get("category") == cat]
        if match:
            grouped[cat] = match
    others = [p for p in patent_list if p.get("category") not in TECH_CATEGORIES]
    if others:
        grouped["기타"] = others
    return grouped

# ==========================================
# 3. HTML 템플릿 (CSS/레이아웃 최적화)
# ==========================================
html_template_str = """
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background-color:#f5f7fa;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fa;">
<tr><td align="center">
<table width="850" cellpadding="0" cellspacing="0" style="background-color:#ffffff; padding:20px; font-family:'Malgun Gothic', sans-serif;">
  <tr>
    <td style="border-bottom:2px solid #005BAC; padding-bottom:10px;">
      <table width="100%">
        <tr>
          <td style="vertical-align:middle;">
            <img src="https://lh3.googleusercontent.com/d/{{ logo_id }}" style="height:45px; vertical-align:middle;">
            <span style="font-size:16px; color:#333; font-weight:bold; margin-left:10px;">부산대학교기술지주주식회사</span>
          </td>
          <td align="right" style="font-size:24px; color:#005BAC; font-weight:bold;">PNUTH Newsletter</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td style="padding:20px 0;"><img src="https://lh3.googleusercontent.com/d/{{ bldg_id }}" width="100%" style="border-radius:10px;"></td></tr>
  <tr>
    <td style="padding-bottom:20px;">
      <h2 style="color:#005BAC; margin-bottom:5px; font-size:26px;">부산대학교 산학협력단 우수 특허/기술 리스트</h2>
      <p style="margin:0; font-size:15px; color:#333; font-weight:bold;">{{ week_date }} 기준 부산대학교 산학협력단 우수 특허</p>
    </td>
  </tr>
  {% for category, patents in grouped_patents.items() %}
  <tr><td style="padding:10px 0 5px 0;"><table width="100%"><tr><td style="background-color:#005BAC; padding:10px 18px; border-radius:6px; color:#ffffff; font-size:17px; font-weight:bold;">▍ {{ category }} 분야</td></tr></table></td></tr>
  <tr><td><table width="100%">
    {% for patent in patents %}
    {% if loop.index0 % 2 == 0 %}<tr>{% endif %}
    <td width="50%" valign="top" style="padding:10px;">
      <table width="100%" style="border:1px solid #ddd; border-radius:10px; min-height:420px;">
        <tr><td style="padding:15px; font-weight:bold; color:#005BAC; font-size:17px; line-height:1.4;">{{ patent.title }} ({{ patent.patent_id }})</td></tr>
        <tr><td align="center"><img src="https://lh3.googleusercontent.com/d/{{ patent.image_id }}" width="220" style="border-radius:10px; border:1px solid #eee;"></td></tr>
        <tr><td style="padding:15px; font-size:14px; line-height:1.7; color:#444;">{% for s in patent.summary %}<p style="margin:0 0 6px 0;">• {{ s }}</p>{% endfor %}</td></tr>
      </table>
    </td>
    {% if loop.index0 % 2 == 1 or loop.last %}</tr>{% endif %}
    {% endfor %}
  </table></td></tr>
  {% endfor %}
  <tr>
    <td align="center" style="padding:40px 10px 20px 10px;">
      <a href="{{ drive_url }}" style="display:block; width:100%; max-width:400px; background-color:#005BAC; color:#ffffff; text-decoration:none; padding:15px 0; border-radius:8px; font-weight:bold; margin-bottom:12px; font-size:16px;">📄 기술요약서(SMK) 전체보기</a>
      <a href="{{ consult_url }}" style="display:block; width:100%; max-width:400px; background-color:#ffffff; color:#005BAC; text-decoration:none; padding:15px 0; border-radius:8px; font-weight:bold; border:2px solid #005BAC; margin-bottom:12px; font-size:16px;">💡 수요기술 상담신청</a>
      <a href="{{ pr_url }}" style="display:block; width:100%; max-width:400px; background-color:#555555; color:#ffffff; text-decoration:none; padding:15px 0; border-radius:8px; font-weight:bold; margin-bottom:12px; font-size:16px;">📺 PNUTH 홍보 채널 바로가기</a>
    </td>
  </tr>
  <tr><td align="center" style="padding-top:20px; font-size:12px; color:gray; line-height:1.5;">부산대학교기술지주주식회사 | 부산광역시 금정구 부산대학로63번길 2<br>문의: 기술이전팀 최정식 과장(051-510-7024)</td></tr>
</table>
</td></tr></table>
</body>
</html>
"""

# ==========================================
# 4. Streamlit 메인 실행부
# ==========================================
def main():
    st.set_page_config(page_title="PNUTH 뉴스레터 생성기", page_icon="🚀")
    
    # temp 폴더 자동 생성
    if not os.path.exists("temp"):
        os.makedirs("temp")

    st.title("🚀 PNUTH 뉴스레터 자동 생성기")
    st.info("행정 직원용: PDF 파일을 업로드하면 뉴스레터용 HTML 파일이 생성됩니다.")
    
    uploaded_files = st.file_uploader("SMK PDF 파일들을 업로드하세요", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("뉴스레터 생성 시작"):
            patent_list = []
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(uploaded_files):
                patent_id = uploaded_file.name.split('_')[0]
                status_placeholder.text(f"⏳ {patent_id} 기술 분석 중... ({idx+1}/{len(uploaded_files)})")
                
                # 파일 임시 저장
                file_path = os.path.join("temp", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 분석 실행
                data = analyze_pdf_document(file_path)
                data['patent_id'] = patent_id
                # 딕셔너리에 없는 번호는 기본 이미지 사용
                data['image_id'] = PATENT_IMAGE_IDS.get(patent_id, "1nhOb0YQTMDT3C5wHat70YfHtsBq3Tiqn")
                
                patent_list.append(data)
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
                # API 안정성을 위해 잠시 대기
                if idx < len(uploaded_files) - 1:
                    time.sleep(2)

            status_placeholder.success("🎉 모든 기술 분석 및 분류가 완료되었습니다!")
            
            # 최종 HTML 생성
            grouped_patents = group_patents_by_category(patent_list)
            now = datetime.datetime.now()
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

            st.divider()
            st.subheader("📋 결과물 다운로드")
            
            # 파일 다운로드 버튼
            st.download_button(
                label="📁 생성된 뉴스레터 HTML 다운로드",
                data=result_html,
                file_name=f"newsletter_{now.strftime('%Y%m%d')}.html",
                mime="text/html"
            )
            
            # 소스코드 복사용 텍스트 영역
            st.text_area("HTML 소스 코드 (복사해서 메일에 사용하세요)", value=result_html, height=300)

if __name__ == "__main__":
    main()
