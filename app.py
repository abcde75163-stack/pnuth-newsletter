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
            "title": "[테스트] 초고강도 하이브리드 금속-플라스틱 결합 신소재 기술 개발",
            "summary": [
                "버튼이 완벽하게 바닥에 고정되는지 확인하기 위한 테스트 모드입니다.",
                "사진은 원본 비율을 유지하며 잘림 없이 깔끔하게 들어갑니다.",
                "내용의 길이가 양쪽이 다르더라도 버튼은 항상 동일한 선상에 맞춰집니다!"
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
# 3. 뉴스레터 HTML 템플릿 (각 구역 높이 철벽 고정!)
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
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
    {% for patent in patents %}
    {% if loop.index0 % 2 == 0 %}<tr>{% endif %}
    
    <td width="48%" valign="top" height="100%" style="border:1px solid #ddd; border-radius:10px; background-color:#ffffff; height:100%;">
      <table width="100%" height="100%" cellpadding="0" cellspacing="0" style="height:100%; min-height:550px;">
        
        <tr>
          <td align="center" valign="top" height="100" style="padding:20px 15px 10px 15px; height:100px; min-height:100px;">
            <p style="margin:0; font-weight:bold; color:#005BAC; font-size:19px; line-height:1.4; text-align:center; letter-spacing:-0.5px; word-break:keep-all;">
              {{ patent.title }}<br><span style="font-size:15px; color:#555; font-weight:bold; letter-spacing:0px;">({{ patent.patent_id }})</span>
            </p>
          </td>
        </tr>
        
        <tr>
          <td align="center" valign="top" height="170" style="padding:0 15px 15px 15px; height:170px;">
            <img src="{{ patent.image_url }}" width="220" height="150" style="width:100%; max-width:280px; height:150px; object-fit:contain; border-radius:10px; border:1px solid #eee; background-color:#fff; display:block;">
          </td>
        </tr>
        
        <tr>
          <td valign="top" style="padding:0 15px; height:100%;">
            <div style="font-size:15px; line-height:1.7; color:#333; word-break:keep-all;">
              {% for s in patent.summary %}
              <p style="margin:0 0 6px 0;">• {{ s }}</p>
              {% endfor %}
            </div>
          </td>
        </tr>
        
        <tr>
          <td valign="bottom" height="70" style="padding:15px; height:70px;">
            <div style="text-align:center; padding-top:15px; border-top:1px dashed #eee;">
              <a href="{{ patent.smk_url }}" target="_blank" style="display:inline-block; background-color:#f0f4f8; color:#005BAC; padding:8px 15px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:14px; border:1px solid #005BAC;">📄 개별 기술요약서(SMK) 보기</a>
            </div>
          </td>
        </tr>
        
      </table>
    </td>
    
    {% if loop.index0 % 2 == 0 %}
      {% if loop.last %}
        <td width="4%"></td><td width="48%"></td>
      {% else %}
        <td width="4%"></td>
      {% endif %}
    {% endif %}
    
    {% if loop.index0 % 2 == 1 or loop.last %}
    </tr>
    <tr><td colspan="3" height="20"></td></tr>
    {% endif %}
    {% endfor %}
    </table>
  </td></tr>
  {% endfor %}
  
  <tr>
    <td align="center" style="padding:30px 10px 20px 10px;">
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
                patent_id = uploaded_file.name.split('_')[0]
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
