import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
import time

# 1. Gemini API 설정
def setup_model():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        # 가용한 모델 중 가장 안정적인 1.5-flash 우선 선택
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        return genai.GenerativeModel(selected)
    except Exception as e:
        st.error(f"모델 초기화 실패: {e}")
        st.stop()

model = setup_model()

# 2. UI 레이아웃
st.set_page_config(page_title="심층 지식 분석기", layout="wide")
st.title("📚 심층 맥락 지식 분석기")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석 키워드", placeholder="예: 뽁뽁이, 최홍만")
    # 개수 조절 옵션 추가 (원하는 만큼 늘릴 수 있게 설정)
    term_count = st.slider("유사 관련어 추출 개수", 5, 20, 12)
    analyze_button = st.button("분석 시작")

# 3. 분석 함수 (개수 파라미터 적용)
def analyze_context(keyword, count):
    prompt = f"""
    키워드 '{keyword}'에 대해 다음 구조의 JSON으로만 답변해.
    
    1. [history]: '{keyword}'의 유래, 개발자, 역사적 배경 (상세히)
    2. [related_terms]: '{keyword}'와 관련된 유사 단어, 기술명, 파생 용어들을 반드시 **{count}개 이상** 추출해.
    3. [attributes]: 핵심 특징 3-5가지.
    4. [examples]: 관련 사례/인물/기업 3-5개.

    {{
        "history": "...",
        "related_terms": ["단어1", "단어2", ..., "단어{count}"],
        "attributes": ["..."],
        "examples": {{"이름": "사유"}}
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(json_match.group()) if json_match else None
    except Exception as e:
        if "429" in str(e): return "RETRY"
        return None

# 4. 결과 출력
if analyze_button and target_keyword:
    with st.spinner("지식 지도를 생성 중입니다..."):
        data = analyze_context(target_keyword, term_count)
        
        if data == "RETRY":
            st.warning("API 요청 제한입니다. 1분 후 다시 시도해주세요.")
        elif data:
            st.subheader(f"📜 {target_keyword}의 유래와 역사")
            st.info(data.get('history'))
            
            st.divider()
            
            # 관련어 출력 (많은 양을 소화하기 위해 태그 클라우드 스타일 적용)
            st.subheader(f"🔗 유사 및 파생 관련어 ({len(data.get('related_terms', []))}개)")
            terms = data.get('related_terms', [])
            
            # 관련어를 보기 좋게 나열 (Markdown 활용)
            term_html = "".join([f'<span style="background-color: #f0f2f6; padding: 5px 10px; margin: 5px; border-radius: 15px; display: inline-block; border: 1px solid #d1d5db;">#{t}</span>' for t in terms])
            st.markdown(term_html, unsafe_allow_html=True)
            
            st.write("") # 간격
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("✨ 핵심 속성")
                for attr in data.get('attributes', []):
                    st.markdown(f"📍 {attr}")
            with col2:
                st.subheader("🌍 관련 사례 및 인물")
                for name, reason in data.get('examples', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
