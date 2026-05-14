def analyze_context(keyword):
    # 사용자님이 원하시는 형식을 프롬프트에 구체적으로 명시합니다.
    prompt = f"""
    입력된 키워드 '{keyword}'에 대해 다음 구조로 분석하여 JSON 형식으로만 답변해.

    1. [history]: '{keyword}'의 유래, 개발자, 역사적 배경 (문장으로 상세히)
    2. [attributes]: '{keyword}'의 핵심 특징 3가지 (짧은 단어)
    3. [related_terms]: '{keyword}'와 직접적으로 관련된 유사 단어나 기술 (에어캡, 포장지 등)
    4. [domestic_international]: '{keyword}'와 맥락이 닿아 있는 국내외 인물이나 기업, 사례

    출력 형식:
    {{
        "history": "유래와 역사 내용",
        "attributes": ["특징1", "특징2", "특징3"],
        "related_terms": ["단어1", "단어2", "단어3"],
        "cases": {{"이름": "사유"}}
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
        st.error(f"분석 중 오류: {e}")
        return None
