import streamlit as st
import os
import time
import datetime
import json
import base64
import requests
import math
from google import genai
from jinja2 import Template

# ==========================================
# 1. 시스템 설정 (Streamlit Secrets 활용)
# ==========================================
# [중요] Streamlit Cloud의 Secrets에 아래 항목들이 등록되어 있어야 합니다.
API_KEY = st.secrets["GEMINI_API_KEY"]
GH_TOKEN = st.secrets["GITHUB_TOKEN"]
GH_REPO = st.secrets["GITHUB_REPO"] # 예: "아이디/저장소이름"

MODEL_ID = "gemini-2.5-flash"
client = genai.Client(api_key=API_KEY)

# 고정 리소스 설정
LOGO_IMAGE_ID = "1WjzjlOOetztrcgq6rioAZxTzi_K-JwLl"
BUILDING_IMAGE_ID = "1f7XwQ2Z-43sECHQ53Of0J8NzqOeRh9Ll"
CONSULT_URL = "https://clever-designers-959477.framer.app/pium-%EA%B8%B0%EC%88%A0%EC%82%AC%EC%97%85%ED%99%94-%EC%84%BC%ED%84%B0-%EC%88%98%EC%9A%94%EA%B8%B0%EC%88%A0-%EC%A0%91%EC%88%98-%ED%8E%98%EC%9D%B4%EC%A7%80"
PR_URL = "https://link.inpock.co.kr/pnutlo?utm_source=ig&utm_medium=social&utm_content=link_in_bio"
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1bgCruhVa2AE_eH1OEq7lbZykQavFlw6S?hl=ko"

TECH_CATEGORIES = ["바이오", "의료기기", "기계", "재료", "전기전자", "정보통신", "에너지자원", "원자력", "건설교통"]

# ==========================================
# 2. 핵심 기능 함수
# ==========================================
def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def upload_to_github(file_obj, patent_id):
    """이미지를 GitHub 저장소의 images/ 폴더에 업로드하고 외부 접근 URL을 반환합니다."""
    file_content = file_obj.getvalue()
    file_name = f"images/{patent_id}.png"
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_name}"
    
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 기존 파일 존재 여부 확인 (SHA 값 획득)
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": f"Upload patent image: {patent_id}",
        "content": base64.b64encode(file_content).decode("utf-8")
    }
    if sha:
        payload["sha"] = sha
    
    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        user_id, repo_name = GH_REPO.split('/')
        # 메일 등 외부에서 직접 접근 가능한 raw 이미지 주소 반환
        return f"https://raw.githubusercontent.com/{user_id}/{repo_name}/main/{file_name}"
    return "https://via.placeholder.com/220?text=Image+Upload+Error"

def analyze_pdf_document(file_obj):
    temp_path = f"temp_{int(time.time())}.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(file_obj.getbuffer())
        with open(temp_path, "rb") as f:
            uploaded_doc = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
        
        prompt = f"""
        특허 마케팅 전문가로서 아래 PDF 내용을 분석하여 JSON 형식으로만 응답하세요.
        항목: title(기업 관점 기술명), summary(특징 3문장 리스트), category({TECH_CATEGORIES} 중 택1)
        형식: {{"title": "기술명", "summary": ["1", "2", "3"], "category": "분야"}}
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        
        try: client.files.delete(name=uploaded_doc.name)
        except: pass
            
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except:
        return {"title": "분석 지연", "summary": ["상세 내용은 SMK를 확인해주세요."], "category": "기타"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

def group_patents_by_category(patent_list):
    grouped = {}
    for cat in TECH_CATEGORIES + ["기타"]:
        match = [p for p in patent_list if p.get("category") == cat]
        if match: grouped[cat] = match
    return grouped

# ==========================================
# 3. HTML 템플릿
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
            <img src="[https://lh3.googleusercontent.com/d/](https://lh3.googleusercontent.com/d/){{ logo_id }}" style="height:45px; vertical-align:middle;">
            <span style="font-size:16px; color:#333; font-weight:bold; margin-left:10px;">부산대학교기술지주주식회사</span>
          </td>
          <td align="right" style="font-size:24px; color:#005BAC; font-weight:bold;">PNUTH Newsletter</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td style="padding:20px 0;"><img src="[https://lh3.googleusercontent.com/d/](https://lh3.googleusercontent.com/d/){{ bldg_id }}" width="100%" style="border-radius:10px;"></td></tr>
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
        <tr><td align="center"><img src="{{ patent.image_url }}" width="220" style="border-radius:10px; border:1px solid #eee;"></td></tr>
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
    if not os.path.exists("temp"): os.makedirs("temp")

    st.title("🚀 PNUTH 뉴스레터 생성기 (GitHub 서버형)")
    st.info("PDF 파일들과 대응하는 이미지 파일들을 함께 업로드하세요. (파일명 번호 일치 필수)")

    col1, col2 = st.columns(2)
    with col1:
        pdf_files = st.file_uploader("1. SMK PDF들", type="pdf", accept_multiple_files=True)
    with col2:
        img_files = st.file_uploader("2. 특허 이미지들", type=["png", "jpg"], accept_multiple_files=True)

    if pdf_files:
        if st.button("뉴스레터 생성 시작"):
            # 이미지 매핑용 딕셔너리 생성
            image_map = {os.path.splitext(img.name)[0]: img for img in img_files}
            
            patent_list = []
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(pdf_files):
                patent_id = uploaded_file.name.split('_')[0]
                status_text.text(f"⏳ {patent_id} 처리 중... ({idx+1}/{len(pdf_files)})")
                
                # AI 분석
                data = analyze_pdf_document(uploaded_file)
                data['patent_id'] = patent_id
                
                # GitHub 서버 업로드 및 URL 획득
                if patent_id in image_map:
                    data['image_url'] = upload_to_github(image_map[patent_id], patent_id)
                else:
                    data['image_url'] = "[https://via.placeholder.com/220?text=No+Image](https://via.placeholder.com/220?text=No+Image)"
                
                patent_list.append(data)
                progress_bar.progress((idx + 1) / len(pdf_files))
                time.sleep(1)

            status_text.success("🎉 분석 및 이미지 서버 전송 완료!")
            progress_bar.empty()

            # HTML 생성 및 다운로드
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
            st.download_button("📂 뉴스레터 HTML 다운로드", data=result_html, file_name=f"newsletter_{now.strftime('%Y%m%d')}.html", mime="text/html")
            st.code(result_html, language="html")
            st.subheader("👀 미리보기")
            st.components.v1.html(result_html, height=800, scrolling=True)

if __name__ == "__main__":
    main()
