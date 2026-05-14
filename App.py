import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re

# 1. Gemini API 설정
try:
    # Streamlit Cloud의 Settings -> Secrets에 설정한 키를 가져옵니다.
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API 키 설정(Secrets)을 확인해주세요.")
    st.stop()

# 2. UI 레이아웃
st.set_page_config(page_title="맥락 분석기", layout="wide")
st.title("🔍 맥락적 관련 검색어 분석기")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석할 키워드 입력", placeholder="예: 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 함수
def analyze_context(keyword):
    prompt = f"""
    '{keyword}'와 관련된 정보를 아래 JSON 형식으로만 답변해줘. 다른 설명은 금지해.
    {{
        "attributes": ["특징1", "특징2"],
        "domestic": {{"인물명": "이유"}},
        "international": {{"인물명": "이유"}},
        "concepts": ["키워드1", "키워드2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 정규표현식을 사용하여 JSON 블록 추출 (따옴표 에러 방지)
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# 4. 결과 출력
if analyze_button and target_keyword:
    with st.spinner("분석 중..."):
        data = analyze_context(target_keyword)
        
        if data:
            st.subheader(f"📌 {target_keyword}의 핵심 특징")
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
        else:
            st.error("데이터를 불러오지 못했습니다.")
