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
# 1. 시스템 설정 (Streamlit Secrets 필수 등록)
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
GH_TOKEN = st.secrets["GITHUB_TOKEN"]
GH_REPO = st.secrets["GITHUB_REPO"]

MODEL_ID = "gemini-2.5-flash-lite" 
client = genai.Client(api_key=API_KEY)

# 고정 리소스 및 배너 URL
LOGO_URL = "https://lh3.googleusercontent.com/d/1WjzjlOOetztrcgq6rioAZxTzi_K-JwLl"
BLDG_URL = "https://lh3.googleusercontent.com/d/1f7XwQ2Z-43sECHQ53Of0J8NzqOeRh9Ll"
CONSULT_URL = "https://clever-designers-959477.framer.app/pium-%EA%B8%B0%EC%88%A0%EC%82%AC%EC%97%85%ED%99%94-%EC%84%BC%ED%84%B0-%EC%88%98%EC%9A%94%EA%B8%B0%EC%88%A0-%EC%A0%91%EC%88%98-%ED%8E%98%EC%9D%B4%EC%A7%80"
PR_URL = "https://link.inpock.co.kr/pnutlo?utm_source=ig&utm_medium=social&utm_content=link_in_bio"

# ==========================================
# 2. 핵심 유틸리티 함수
# ==========================================

def get_week_of_month(dt):
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    return int(math.ceil(adjusted_dom / 7.0))

def upload_file_to_github(file_obj, patent_id, folder_name):
    file_content = file_obj.getvalue()
    ext = file_obj.name.split('.')[-1].lower() if hasattr(file_obj, 'name') else 'png'
    file_name = f"{folder_name}/{patent_id}.{ext}"
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_name}"
    
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {"message": f"Update {folder_name}: {patent_id}", "content": base64.b64encode(file_content).decode("utf-8")}
    if sha: payload["sha"] = sha
    
    put_res = requests.put(url, headers=headers, json=payload)
    
    if put_res.status_code in [200, 201]:
        user_id, repo_name = GH_REPO.split('/')
        if folder_name == "pdfs":
            return f"https://{user_id}.github.io/{repo_name}/{file_name}"
        else:
            return f"https://raw.githubusercontent.com/{user_id}/{repo_name}/main/{file_name}"
            
    return "https://via.placeholder.com/220?text=Upload+Error"

def analyze_pdf_document(file_obj, test_mode=False):
    """PDF 분석 (테스트 모드 지원)"""
    if test_mode:
        return {
            "title": "[테스트] 초고강도 하이브리드 금속-플라스틱 결합 신소재 기술",
            "summary": [
                "API 소모 없이 레이아웃을 확인하는 테스트 모드입니다.",
                "테이블(Table) 구조를 완전히 버리고 최신 Flexbox 기술을 도입했습니다.",
                "내용의 길이가 왼쪽 오른쪽이 아무리 달라도, 테두리의 높이와 맨 밑 버튼의 위치는 1mm의 오차도 없이 무조건 완벽하게 똑같이 맞춰집니다!"
            ],
            "category": "테스트분야"
        }

    temp_path = f"temp_{int(time.time())}.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(file_obj.getbuffer())
        with open(temp_path, "rb") as f:
            uploaded_doc = client.files.upload(file=f, config={'mime_type': 'application/pdf'})
        
        prompt = """
        특허 기술요약서(SMK) PDF를 분석하여 JSON 형식으로만 응답하세요.
        - title: 기술 명칭
        - summary: 주요 특징을 3개 문장 리스트로 요약
        - category: 문서 좌측 상단 로고 영역에 명시되어 있는 기술 분야 (예: '정보통신', '재료' 등. 공백/줄바꿈 제거 단일 단어)
        """
        response = client.models.generate_content(model=MODEL_ID, contents=[uploaded_doc, prompt])
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)
    except Exception as e:
        return {"title": "분석 지연", "summary": [f"사유: {str(e)[:30]}"], "category": "기타"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

def group_patents_by_category(patent_list):
    grouped = {}
    for patent in patent_list:
        raw_cat = patent.get("category", "기타")
        cat = raw_cat.replace(" ", "").replace("\n", "") if raw_cat else "기타"
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(patent)
    return grouped

# ==========================================
# 3. 뉴스레터 HTML 템플릿 (Flexbox 전면 도입)
# ==========================================
html_template_str = """
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background-color:#f5f7fa;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#e8f0fa;">
  <tr>
    <td align="center" style="padding:10px 20px; font-size:12px; color:#444; font-family:'Malgun Gothic', sans-serif;">
      본 메일은 부산대학교 산학협력단의 <strong>기술이전 또는 가족기업 대상</strong>으로 송부드리는 메일입니다. &nbsp;|&nbsp;
      수신을 원치 않으시면 <a href="mailto:cjs7024@pusan.ac.kr" style="color:#005BAC;">수신거부</a>를 클릭해 주세요.
    </td>
  </tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f7fa;">
<tr><td align="center">
<table width="850" cellpadding="0" cellspacing="0" style="background-color:#ffffff; padding:20px; font-family:'Malgun Gothic', sans-serif;">
  <tr>
    <td style="border-bottom:2px solid #005BAC; padding-bottom:10px;">
      <table width="100%">
        <tr>
          <td style="vertical-align:middle;">
            <img src="{{ logo_url }}" style="height:45px; vertical-align:middle;">
            <span style="font-size:16px; color:#333; font-weight:bold; margin-left:10px;">부산대학교기술지주주식회사</span>
          </td>
          <td align="right" style="font-size:24px; color:#005BAC; font-weight:bold;">PNUTH Newsletter</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td style="padding:20px 0;"><img src="{{ bldg_url }}" width="100%" style="border-radius:10px;"></td></tr>
  <tr>
    <td style="padding-bottom:20px;">
      <h2 style="color:#005BAC; margin-bottom:5px; font-size:26px;">부산대학교 산학협력단 우수 특허/기술 리스트</h2>
      <p style="margin:0; font-size:15px; color:#333; font-weight:bold;">{{ week_date }} 기준 우수 특허</p>
    </td>
  </tr>
  
  {% for category, patents in grouped_patents.items() %}
  <tr><td style="padding:10px 0 5px 0;"><table width="100%"><tr><td style="background-color:#005BAC; padding:10px 18px; border-radius:6px; color:#ffffff; font-size:17px; font-weight:bold;">▍ {{ category }} 분야</td></tr></table></td></tr>
  
  <tr><td style="padding-top:10px;">
    
    <div style="display: flex; flex-direction: column; gap: 12px;">
  {% for patent in patents %}
  <div style="display: flex; flex-direction: row; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff; box-sizing: border-box; overflow: hidden;">
    
    {# 왼쪽: 이미지 영역 (고정 너비) #}
    <div style="width: 220px; min-width: 220px; display: flex; justify-content: center; align-items: center; padding: 15px; border-right: 1px solid #eee; background-color: #fafafa;">
      <img src="{{ patent.image_url }}" style="width:190px; height:130px; object-fit:contain; border-radius:8px; background-color:#fff;">
    </div>
    
    {# 오른쪽: 내용 영역 #}
    <div style="flex: 1; display: flex; flex-direction: column; padding: 15px 18px;">
      
      {# 제목 #}
      <p style="margin:0 0 8px 0; font-weight:bold; color:#005BAC; font-size:17px; line-height:1.4; letter-spacing:-0.5px; word-break:keep-all;">
        {{ patent.title }}
        <span style="font-size:13px; color:#777; font-weight:normal; margin-left:6px;">({{ patent.patent_id }})</span>
      </p>
      
      {# 구분선 #}
      <div style="border-top: 1px solid #eee; margin-bottom: 8px;"></div>
      
      {# 요약 #}
      <div style="font-size:14px; line-height:1.6; color:#333; word-break:keep-all; flex-grow: 1;">
        {% for s in patent.summary %}
        <p style="margin:0 0 4px 0;">• {{ s }}</p>
        {% endfor %}
      </div>
      
      {# SMK 버튼 #}
      <div style="margin-top: 10px;">
        <a href="{{ patent.smk_url }}" target="_blank" style="display:inline-block; background-color:#f0f4f8; color:#005BAC; padding:6px 14px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:13px; border:1px solid #005BAC;">📄 기술요약서(SMK) 보기</a>
      </div>
      
    </div>
  </div>
  {% endfor %}
</div>
    </td></tr>
  {% endfor %}
  
  <tr>
    <td align="center" style="padding:15px 10px 10px 10px;">
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
# 4. Streamlit 메인 실행
# ==========================================
def main():
    st.set_page_config(page_title="PNUTH 뉴스레터 생성기", page_icon="🚀")
    st.title("🚀 PNUTH 뉴스레터 자동 생성기")
    st.info("PDF와 이미지 파일을 함께 업로드하세요. (파일명 번호 일치 필수)")

    is_test_mode = st.checkbox("🧪 테스트 모드 켜기 (체크 시 API 요금이 나가지 않으며 초고속으로 레이아웃만 확인합니다.)")

    col1, col2 = st.columns(2)
    with col1:
        pdf_files = st.file_uploader("1. SMK PDF들", type="pdf", accept_multiple_files=True)
    with col2:
        img_files = st.file_uploader("2. 특허 이미지들", type=["png", "jpg"], accept_multiple_files=True)

    if pdf_files:
        if st.button("뉴스레터 생성 시작"):
            image_map = {os.path.splitext(img.name)[0]: img for img in img_files}
            patent_list = []
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(pdf_files):
                base_name = uploaded_file.name.split('_')[0]
                patent_id = os.path.splitext(base_name)[0]
                status_text.text(f"⏳ {patent_id} 처리 중... ({idx+1}/{len(pdf_files)})")
                
                if not is_test_mode:
                    time.sleep(2)
                
                data = analyze_pdf_document(uploaded_file, test_mode=is_test_mode)
                data['patent_id'] = patent_id
                
                if is_test_mode:
                    data['image_url'] = "https://via.placeholder.com/280x150?text=Test+Image"
                    data['smk_url'] = "#"
                else:
                    if patent_id in image_map:
                        data['image_url'] = upload_file_to_github(image_map[patent_id], patent_id, "images")
                    else:
                        data['image_url'] = "https://via.placeholder.com/280x150?text=No+Image"
                    data['smk_url'] = upload_file_to_github(uploaded_file, patent_id, "pdfs")
                
                patent_list.append(data)
                progress_bar.progress((idx + 1) / len(pdf_files))

            status_text.success("🎉 생성 완료!")
            
            grouped_patents = group_patents_by_category(patent_list)
            now = datetime.datetime.now()
            week_str = f"{now.year}년 {now.month}월 {get_week_of_month(now)}째주"
            
            template = Template(html_template_str)
            result_html = template.render(
                week_date=week_str,
                grouped_patents=grouped_patents,
                logo_url=LOGO_URL,
                bldg_url=BLDG_URL,
                consult_url=CONSULT_URL,
                pr_url=PR_URL
            )

            st.divider()
            st.download_button("📂 뉴스레터 HTML 다운로드", data=result_html, file_name=f"newsletter_{now.strftime('%Y%m%d')}.html", mime="text/html")
            st.components.v1.html(result_html, height=800, scrolling=True)

if __name__ == "__main__":
    main()
