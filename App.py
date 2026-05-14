import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re

# 1. Gemini API 설정 및 가용 모델 자동 검색
def setup_model():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Streamlit Secrets에 'GOOGLE_API_KEY'를 설정해주세요.")
            st.stop()
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 내 API 키가 권한을 가진 모델 리스트를 가져옵니다.
        # 404 에러를 방지하기 위해 'generateContent'가 가능한 모델만 필터링합니다.
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # 선호하는 모델 순서 (최신 순)
        priority_list = [
            'models/gemini-1.5-flash', 
            'models/gemini-1.5-flash-latest', 
            'models/gemini-pro'
        ]
        
        selected_model_name = None
        for preferred in priority_list:
            if preferred in available_models:
                selected_model_name = preferred
                break
        
        # 만약 선호 모델이 리스트에 없다면 사용 가능한 첫 번째 모델 선택
        if not selected_model_name:
            if available_models:
                selected_model_name = available_models[0]
            else:
                st.error("현재 API 키로 사용할 수 있는 Gemini 모델이 없습니다.")
                st.stop()
        
        # 선택된 모델 로그 출력 (디버깅용)
        # st.toast(f"연결된 모델: {selected_model_name}") 
        return genai.GenerativeModel(selected_model_name)
        
    except Exception as e:
        st.error(f"모델 초기화 실패: {e}")
        st.info("API 키를 새로 발급받아 Secrets에 다시 입력해보세요.")
        st.stop()

# 모델 초기 실행
model = setup_model()

# 2. UI 레이아웃
st.set_page_config(page_title="맥락 데이터 분석기", layout="wide")
st.title("🔍 맥락적 관련 검색어 분석기")
st.write("단순 키워드를 넘어 인물의 맥락과 유사 사례를 분석합니다.")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석 키워드 입력", placeholder="예: 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 함수
def analyze_context(keyword):
    prompt = f"""
    Analyze the keyword '{keyword}' and provide related information in JSON format ONLY.
    {{
        "attributes": ["핵심특징1", "핵심특징2", "핵심특징3"],
        "domestic": {{
            "유사 한국인물1": "이유 및 공통점",
            "유사 한국인물2": "이유 및 공통점"
        }},
        "international": {{
            "유사 해외인물1": "이유 및 공통점",
            "유사 해외인물2": "이유 및 공통점"
        }},
        "concepts": ["관련 전문용어1", "관련 학술개념2"]
    }}
    Ensure all values are written in Korean. Do not include any explanation outside of JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # JSON 블록 { ... } 추출 (정규표현식)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            st.warning("데이터 정제 실패. AI 응답 원문을 표시합니다.")
            st.code(content)
            return None
            
    except Exception as e:
        st.error(f"분석 도중 오류가 발생했습니다: {e}")
        return None

# 4. 결과 출력
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 데이터를 심층 분석 중입니다..."):
        data = analyze_context(target_keyword)
        
        if data:
            # 핵심 속성
            st.subheader(f"📌 {target_keyword} 핵심 속성")
            cols = st.columns(len(data.get('attributes', [])))
            for i, attr in enumerate(data.get('attributes', [])):
                cols[i].success(f"**{attr}**")
            
            st.divider()
            
            # 유사 사례 비교
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🇰🇷 국내 유사 맥락")
                for name, reason in data.get('domestic', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            with col2:
                st.subheader("🌎 해외 유사 사례")
                for name, reason in data.get('international', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            st.divider()
            
            # 관련 개념 및 표 요약
            st.subheader("💡 관련 개념 및 학술 키워드")
            st.info(", ".join(data.get('concepts', [])))
            
            st.subheader("📊 분석 데이터 요약")
            all_data = {**data.get('domestic', {}), **data.get('international', {})}
            df = pd.DataFrame([{"대상": k, "분석 맥락": v} for k, v in all_data.items()])
            st.table(df)
