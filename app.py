import streamlit as st
import os
import datetime
from jinja2 import Template

# [기존 설정 및 함수들 유지: API_KEY, analyze_pdf_document, html_template_str 등]

def main():
    st.set_page_config(page_title="PNUTH 뉴스레터 생성기", page_icon="🚀")
    
# [추가] temp 폴더가 없으면 자동으로 생성하는 로직
    if not os.path.exists("temp"):
        os.makedirs("temp")

    st.title("🚀 PNUTH 뉴스레터 자동 생성기")
    st.info("행정 직원용: PDF 파일을 업로드하면 뉴스레터 HTML 코드가 생성됩니다.")

    # 1. 파일 업로드 섹션
    uploaded_files = st.file_uploader("특허 SMK PDF 파일들을 선택하세요 (다중 선택 가능)", 
                                    type="pdf", accept_multiple_files=True)

    if uploaded_files:
        st.write(f"✅ 총 {len(uploaded_files)}개의 파일이 선택되었습니다.")
        
        if st.button("뉴스레터 생성 시작"):
            patent_list = []
            progress_bar = st.progress(0)
            
            for idx, uploaded_file in enumerate(uploaded_files):
                # 임시 파일 저장 및 분석 로직
                with open(os.path.join("temp", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                patent_id = uploaded_file.name.split('_')[0]
                st.write(f"🔍 {patent_id} 분석 중...")
                
                # 분석 함수 호출 (기존 analyze_pdf_document 활용)
                data = analyze_pdf_document(os.path.join("temp", uploaded_file.name))
                data['patent_id'] = patent_id
                data['image_id'] = PATENT_IMAGE_IDS.get(patent_id, "")
                patent_list.append(data)
                
                # 진행률 업데이트
                progress_bar.progress((idx + 1) / len(uploaded_files))

            # HTML 생성
            grouped_patents = group_patents_by_category(patent_list)
            now = datetime.datetime.now()
            week_str = f"{now.year}년 {now.month}월 {get_week_of_month(now)}째주"
            
            template = Template(html_template_str)
            result_html = template.render(
                week_date=week_str,
                grouped_patents=grouped_patents,
                # ... 기타 변수들
            )

            # 2. 결과물 출력 및 다운로드
            st.success("🎉 뉴스레터 생성이 완료되었습니다!")
            
            # HTML 미리보기 (직원분이 복사하기 편하도록)
            st.subheader("📋 생성된 HTML 코드 (복사해서 메일에 붙여넣으세요)")
            st.code(result_html, language='html')
            
            # 파일로 다운로드 버튼
            st.download_button(
                label="HTML 파일로 다운로드",
                data=result_html,
                file_name=f"newsletter_{now.strftime('%Y%m%d')}.html",
                mime="text/html"
            )

if __name__ == "__main__":
    main()