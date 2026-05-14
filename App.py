import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Gemini API 설정
# 본인의 API 키를 입력하세요.
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. Streamlit UI 설정
st.set_page_config(page_title="Context Keyword Analyzer", layout="wide")

st.title("🔍 맥락적 관련 검색어 분석기")
st.write("단순 검색어를 넘어, 인물의 특징과 맥락을 분석하여 유사 사례와 인물을 추천합니다.")

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    target_keyword = st.text_input("분석할 키워드(인물) 입력", placeholder="예: 최홍만")
    analyze_button = st.button("분석 시작")

# 3. 분석 로직
def analyze_context(keyword):
    # AI에게 전달할 프롬프트 - 맥락적 분석을 위해 구체적으로 지시
    prompt = f"""
    입력된 키워드 '{keyword}'에 대해 다음 4가지 카테고리로 연관 정보를 분석해줘.
    결과는 반드시 아래의 JSON 형식을 지켜서 출력해.

    1. [Attributes]: {keyword}의 핵심 특징 (예: 거인증, 씨름, 격투기, 방송인)
    2. [Domestic]: 유사한 맥락을 가진 한국 인물 및 이유
    3. [International]: 유사한 맥락을 가진 해외 인물 및 이유 (예: 로버트 워들로 등)
    4. [Concepts]: 이와 관련된 학술적/문화적 키워드 (예: 기네스북, 말단비대증, 스포테이너)

    출력 형식:
    {{
        "attributes": ["특징1", "특징2"],
        "domestic": {{"인물명": "이유", "인물명": "이유"}},
        "international": {{"인물명": "이유", "인물명": "이유"}},
        "concepts": ["키워드1", "키워드2"]
    }}
    """
    
    response = model.generate_content(prompt)
    try:
        # 응답 텍스트에서 JSON 부분만 추출 (간혹 AI가 설명을 붙일 수 있음)
        import json
        res_text = response.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("
```json")[1].split("```")[0]
        return json.loads(res_text)
    except:
        return None

# 4. 결과 출력
if analyze_button and target_keyword:
    with st.spinner(f"'{target_keyword}'의 맥락을 분석 중입니다..."):
        data = analyze_context(target_keyword)
        
        if data:
            # 상단 핵심 태그 표시
            st.subheader(f"📌 {target_keyword}의 핵심 특징")
            cols = st.columns(len(data['attributes']))
            for i, attr in enumerate(data['attributes']):
                cols[i].info(f"**{attr}**")

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🇰🇷 국내 유사 사례")
                for name, reason in data['domestic'].items():
                    with st.expander(f"**{name}**"):
                        st.write(reason)

                st.subheader("💡 관련 개념/키워드")
                st.write(", ".join(data['concepts']))

            with col2:
                st.subheader("🌎 해외 유사 사례 & 기네스")
                for name, reason in data['international'].items():
                    with st.expander(f"**{name}** (해외)"):
                        st.write(reason)
            
            # 데이터 분석용 표 제공
            st.divider()
            st.subheader("📊 분석 데이터 요약")
            df_list = []
            for name, reason in {**data['domestic'], **data['international']}.items():
                df_list.append({"대상": name, "연관 맥락": reason})
            st.table(pd.DataFrame(df_list))
            
        else:
            st.error("분석 결과를 가져오는데 실패했습니다. 다시 시도해주세요.")
