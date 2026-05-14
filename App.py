import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re

# 1. Gemini API 설정
def setup_model():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Streamlit Secrets에 'GOOGLE_API_KEY'가 설정되지 않았습니다.")
            st.stop()
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 404 에러를 피하기 위해 가장 범용적이고 안정적인 'gemini-pro' 모델을 우선 사용합니다.
        # 만약 1.5 flash를 꼭 쓰고 싶다면 'models/gemini-1.5-flash'라고 전체 경로를 적기도 합니다.
        return genai.GenerativeModel('gemini-pro')
        
    except Exception as e:
        st.error(f"모델 설정 중 오류 발생: {e}")
        st.stop()

model = setup_model()

# 2. UI 설정
st.set_page_config(page_title="맥락 데이터 분석기", layout="wide")
st.title("🔍 맥락적 관련 검색어 분석기")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석할 키워드 입력", placeholder="예: 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 함수
def analyze_context(keyword):
    # AI가 JSON 형식만 깔끔하게 내보내도록 유도
    prompt = f"""
    Analyze the keyword '{keyword}' and provide related information in JSON format ONLY.
    
    {{
        "attributes": ["key_feature1", "key_feature2"],
        "domestic": {{"Korean_person_name": "reason"}},
        "international": {{"International_person_name": "reason"}},
        "concepts": ["related_concept1", "related_concept2"]
    }}
    
    Ensure the reasons are in Korean. Do not include any other text.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # 정규표현식으로 JSON 블록 { ... } 만 추출하여 구문 오류 방지
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            st.error("AI 응답에서 JSON 형식을 찾을 수 없습니다.")
            return None
    except Exception as e:
        st.error(f"분석 중 오류 발생 (404 등): {e}")
        st.info("Tip: API 키가 해당 모델을 지원하는지 확인하거나, 모델명을 'gemini-pro'로 변경해 보세요.")
        return None

# 4. 결과 화면
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 맥락 데이터를 분석 중..."):
        data = analyze_context(target_keyword)
        
        if data:
            st.subheader(f"📌 {target_keyword}의 주요 속성")
            st.write(", ".join(data.get('attributes', [])))
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🇰🇷 국내 유사 사례")
                for name, reason in data.get('domestic', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            with col2:
                st.subheader("🌎 해외 유사 사례")
                for name, reason in data.get('international', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            st.divider()
            st.subheader("💡 관련 개념")
            st.info(", ".join(data.get('concepts', [])))
