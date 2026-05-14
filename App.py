import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re

# 1. Gemini API 설정 및 가용 모델 자동 검색 (404 에러 방지)
def setup_model():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("Streamlit Secrets에 'GOOGLE_API_KEY'를 설정해주세요.")
            st.stop()
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 가용한 모델 리스트 확인
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # 선호 모델 순위
        priority_list = ['models/gemini-1.5-flash', 'models/gemini-pro']
        selected_model_name = next((p for p in priority_list if p in available_models), 
                                   available_models[0] if available_models else None)
        
        if not selected_model_name:
            st.error("가용한 Gemini 모델이 없습니다.")
            st.stop()
            
        return genai.GenerativeModel(selected_model_name)
    except Exception as e:
        st.error(f"모델 초기화 실패: {e}")
        st.stop()

model = setup_model()

# 2. UI 레이아웃 설정
st.set_page_config(page_title="맥락적 지식 분석기", layout="wide")
st.title("📚 맥락적 지식 분석기 (유래/역사/관련어)")
st.write("키워드의 역사적 유래부터 관련 용어까지 심층적으로 분석합니다.")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석 키워드 입력", placeholder="예: 뽁뽁이, 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 로직 함수 (프롬프트 강화)
def analyze_context(keyword):
    prompt = f"""
    입력된 키워드 '{keyword}'에 대해 다음 구조로 분석하여 JSON 형식으로만 답변해. 
    마크다운 기호 없이 순수 JSON만 출력해.

    1. [history]: '{keyword}'의 유래, 개발자(존재 시), 역사적 배경을 2~3문장으로 상세히 설명.
    2. [related_terms]: '{keyword}'와 직접적으로 관련된 유사 단어나 기술적 명칭 (3~5개).
    3. [attributes]: '{keyword}'를 정의하는 핵심 특징 (3가지).
    4. [examples]: '{keyword}'와 맥락이 닿아 있는 국내외 사례나 인물, 기업 (3개).

    출력 형식:
    {{
        "history": "역사와 유래 설명 내용",
        "related_terms": ["단어1", "단어2", "단어3"],
        "attributes": ["특징1", "특징2", "특징3"],
        "examples": {{"이름": "사유", "이름": "사유"}}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # JSON 추출
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return None
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        return None

# 4. 결과 출력 레이아웃
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 역사를 찾는 중..."):
        data = analyze_context(target_keyword)
        
        if data:
            # 1. 유래 및 역사 (가장 상단 배치)
            st.subheader(f"📜 {target_keyword}의 유래와 역사")
            st.info(data.get('history', '관련 역사 정보가 없습니다.'))
            
            st.divider()

            col1, col2 = st.columns(2)
            
            with col1:
                # 2. 유사 관련어
                st.subheader("🔗 유사 관련어")
                terms = data.get('related_terms', [])
                if terms:
                    # 해시태그 스타일로 표시
                    st.write(" ".join([f"**#{t}**" for t in terms]))
                
                st.write("") # 간격 조절
                
                # 3. 핵심 특징
                st.subheader("✨ 핵심 속성")
                for attr in data.get('attributes', []):
                    st.markdown(f"✅ {attr}")

            with col2:
                # 4. 관련 사례 및 인물
                st.subheader("🌍 관련 사례 및 인물")
                for name, reason in data.get('examples', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
            
            # 하단 데이터 테이블 요약
            st.divider()
            st.subheader("📊 데이터 분석 요약")
            df_data = [{"카테고리": "관련어", "내용": ", ".join(data.get('related_terms', []))},
                       {"카테고리": "핵심특징", "내용": ", ".join(data.get('attributes', []))}]
            st.table(pd.DataFrame(df_data))
            
        else:
            st.error("데이터 분석에 실패했습니다. 다시 시도해 주세요.")
