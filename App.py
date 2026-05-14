def analyze_context(keyword):
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
    
    try:
        response = model.generate_content(prompt)
        import json
        res_text = response.text.strip()
        
        # 에러가 났던 부분: 마크다운 기호를 제거하고 JSON만 추출하는 로직
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0]
        elif "```" in res_text:
            res_text = res_text.split("
```")[1].split("```")[0]
            
        return json.loads(res_text)
    except Exception as e:
        st.error(f"분석 중 에러가 발생했습니다: {e}")
        return None
