import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
import time

# 1. Gemini API 설정 및 가용 모델 자동 검색
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
        
        # 429 에러가 덜 발생하는 모델 순위 (보통 flash 계열이 제한이 넉넉합니다)
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
st.title("📚 맥락적 지식 분석기")
st.write("키워드의 역사적 유래부터 관련 용어까지 분석합니다. (무료 티어는 분당 요청 횟수가 제한됩니다)")

with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석 키워드 입력", placeholder="예: 뽁뽁이, 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 로직 함수 (429 에러 대응 추가)
def analyze_context(keyword):
    prompt = f"""
    입력된 키워드 '{keyword}'에 대해 다음 구조로 분석하여 JSON 형식으로만 답변해. 
    마크다운 기호 없이 순수 JSON만 출력해.

    1. [history]: '{keyword}'의 유래, 개발자, 역사적 배경을 상세히 설명.
    2. [related_terms]: '{keyword}'와 관련된 유사 단어나 기술적 명칭 (3~5개).
    3. [attributes]: '{keyword}'를 정의하는 핵심 특징 (3가지).
    4. [examples]: '{keyword}'와 맥락이 닿아 있는 사례나 인물 (3개).

    출력 형식:
    {{
        "history": "내용",
        "related_terms": ["단어1", "단어2"],
        "attributes": ["특징1", "특징2"],
        "examples": {{"이름": "사유"}}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None

    except Exception as e:
        # 429 에러(Quota Exceeded) 발생 시 처리
        if "429" in str(e):
            st.warning("⚠️ API 요청 제한(분당 5회)을 초과했습니다. 약 1분 후 자동으로 재시도합니다. 잠시만 기다려주세요...")
            time.sleep(60) # 60초 대기 후 재시도 시 유용 (여기서는 직접 재시도 대신 안내 후 종료)
            return "RETRY_NEEDED"
        else:
            st.error(f"분석 중 오류 발생: {e}")
            return None

# 4. 결과 출력
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 데이터를 심층 분석 중..."):
        data = analyze_context(target_keyword)
        
        if data == "RETRY_NEEDED":
            st.info("요청 제한을 피하기 위해 잠시 후 다시 '분석 시작' 버튼을 눌러주세요.")
        elif data:
            # 유래 및 역사
            st.subheader(f"📜 {target_keyword}의 유래와 역사")
            st.info(data.get('history', '관련 정보가 없습니다.'))
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔗 유사 관련어")
                terms = data.get('related_terms', [])
                st.write(" ".join([f"**#{t}**" for t in terms]))
                
                st.subheader("✨ 핵심 속성")
                for attr in data.get('attributes', []):
                    st.markdown(f"✅ {attr}")

            with col2:
                st.subheader("🌍 관련 사례 및 인물")
                for name, reason in data.get('examples', {}).items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)
        else:
            st.error("데이터 분석에 실패했습니다.")
