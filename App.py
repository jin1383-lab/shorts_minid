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
        
        # 404 에러 방지를 위해 가장 범용적인 모델 명칭 사용
        # 최신 라이브러리 환경에서는 gemini-1.5-flash가 권장됩니다.
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"모델 설정 중 오류 발생: {e}")
        st.stop()

model = setup_model()

# 2. UI 설정
st.set_page_config(page_title="맥락 분석 도구", layout="wide")
st.title("🔍 맥락적 관련 검색어 분석기")
st.write("인물의 특징을 분석하여 국내외 유사 사례와 기네스급 정보를 연결합니다.")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석할 키워드 입력", placeholder="예: 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 함수
def analyze_context(keyword):
    # AI가 JSON 형식만 깔끔하게 내보내도록 유도하는 프롬프트
    prompt = f"""
    입력된 키워드 '{keyword}'를 분석하여 반드시 아래 JSON 형식으로만 응답하세요.
    
    {{
        "attributes": ["핵심특징1", "핵심특징2"],
        "domestic": {{"유사인물1": "이유", "유사인물2": "이유"}},
        "international": {{"유사인물1": "이유", "유사인물2": "이유"}},
        "concepts": ["관련개념1", "관련개념2"]
    }}
    
    다른 설명은 절대 생략하고 JSON 데이터만 출력하세요.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # 정규표현식으로 JSON 블록만 추출 (구문 오류 방지)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # JSON 형식이 아닐 경우 재시도 로직이나 에러 처리
            st.error("AI가 올바른 JSON 형식을 생성하지 못했습니다.")
            return None
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        return None

# 4. 결과 화면
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 맥락 데이터를 수집 중..."):
        data = analyze_context(target_keyword)
        
        if data:
            # 1. 핵심 특징 (태그 형태)
            st.subheader(f"📌 {target_keyword}의 주요 속성")
            attrs = data.get('attributes', [])
            if attrs:
                cols = st.columns(len(attrs))
                for i, val in enumerate(attrs):
                    cols[i].success(f"**{val}**")
            
            st.divider()
            
            # 2. 국내외 유사 사례 비교
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🇰🇷 국내 유사 맥락 인물")
                for name, reason in data.get('domestic', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            with col2:
                st.subheader("🌎 해외 유사 사례 & 기네스")
                for name, reason in data.get('international', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            st.divider()
            
            # 3. 데이터 요약 테이블
            st.subheader("📊 데이터 분석 요약")
            all_cases = {**data.get('domestic', {}), **data.get('international', {})}
            df_rows = [{"인물/대상": k, "연관 사유": v} for k, v in all_cases.items()]
            if df_rows:
                st.table(pd.DataFrame(df_rows))
                
            # 4. 하단 관련 개념
            st.caption(f"관련 개념: {', '.join(data.get('concepts', []))}")
