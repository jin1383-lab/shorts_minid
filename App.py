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
        
        # 404 에러를 방지하기 위해 'models/' 경로를 명시합니다.
        # 가장 안정적인 gemini-1.5-flash 또는 gemini-pro를 시도합니다.
        return genai.GenerativeModel('models/gemini-1.5-flash')
        
    except Exception as e:
        # 만약 1.5-flash도 안된다면 gemini-pro로 마지막 시도
        try:
            return genai.GenerativeModel('models/gemini-pro')
        except:
            st.error(f"모델 로드 실패: {e}")
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
    prompt = f"""
    Analyze the keyword '{keyword}' and provide related information in JSON format ONLY.
    {{
        "attributes": ["key_feature1", "key_feature2"],
        "domestic": {{"Korean_person_name": "reason"}},
        "international": {{"International_person_name": "reason"}},
        "concepts": ["related_concept1", "related_concept2"]
    }}
    Ensure all reasons and descriptions are in Korean.
    """
    
    try:
        # 안전한 호출을 위해 명시적으로 generate_content 사용
        response = model.generate_content(prompt)
        
        # API 응답 확인
        if not response.text:
            st.error("AI로부터 응답을 받지 못했습니다.")
            return None
            
        content = response.text
        
        # JSON 블록 추출
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # JSON 형식이 아닐 경우 텍스트라도 표시하기 위해 예외 처리
            st.warning("데이터 형식 변환에 실패했습니다. 응답 원문을 확인하세요.")
            st.write(content)
            return None
            
    except Exception as e:
        st.error(f"분석 실행 중 오류 발생: {e}")
        return None

# 4. 결과 화면
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 맥락을 분석 중입니다..."):
        data = analyze_context(target_keyword)
        
        if data:
            st.subheader(f"📌 {target_keyword}의 주요 속성")
            st.info(", ".join(data.get('attributes', [])))
            
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
            st.write(", ".join(data.get('concepts', [])))
