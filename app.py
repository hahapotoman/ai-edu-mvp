import streamlit as st
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="AI 학습 파트너", page_icon="📚")
st.title("🤖 AI 학습 파트너 MVP")
st.markdown("학습 주제와 난이도를 입력하면 맞춤형 개념 설명과 **인터랙티브 퀴즈**를 생성해 드립니다.")

with st.sidebar:
    st.header("⚙️ 설정")
    difficulty = st.selectbox("난이도 선택", ["초급", "중급", "고급"])
    if st.button("🔄 학습 초기화"):
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.rerun()

topic = st.text_input("📖 학습할 주제나 개념을 입력하세요 (예: 미적분 도함수, 영어 관용구)")

if topic and st.button("🚀 AI 학습 자료 생성"):
    with st.spinner("AI가 맞춤형 자료를 생성 중입니다..."):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-3.5-flash')

            prompt = f"""당신은 [{topic}] 전문가 교사입니다. 다음 학습자를 위해 JSON 형식으로만 답변하세요 (마크다운 백틱 제외):

📌 학습자 수준: {difficulty}
📘 주제: {topic}

JSON 구조:
{{
  "summary": "3문장 이내 개념 요약 (비유 포함)",
  "quiz": [
    {{"q": "객관식 문제 1", "options": ["A", "B", "C", "D"], "correct": 0}},
    {{"q": "객관식 문제 2", "options": ["A", "B", "C", "D"], "correct": 1}},
    {{"q": "객관식 문제 3", "options": ["A", "B", "C", "D"], "correct": 2}},
    {{"q": "주관식 문제 (간단한 답)", "options": [], "correct": -1}}
  ],
  "tips": "오답 시 학습 팁 1문장"
}}

정답 인덱스는 options 배열 기준 (0부터 시작). 주관식은 correct: -1."""

            response = model.generate_content(prompt)
            clean_text = re.sub(r'```json\s*|\s*```', '', response.text).strip()
            data = json.loads(clean_text)

            st.session_state.quiz_data = data
            st.session_state.user_answers = {}
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ AI 호출 또는 JSON 파싱 오류:\n{e}")

if st.session_state.get("quiz_data"):
    data = st.session_state.quiz_data
    st.markdown(f"📘 **개념 요약**\n{data['summary']}")
    st.divider()

    for i, q in enumerate(data["quiz"]):
        st.subheader(f"Q{i+1}. {q['q']}")
        if q["options"]:
            ans = st.radio("정답을 선택하세요", options=q["options"], key=f"q_{i}")
            st.session_state.user_answers[f"q_{i}"] = ans
        else:
            ans = st.text_input(f"Q{i+1} 주관식 답안 입력", key=f"q_{i}")
            st.session_state.user_answers[f"q_{i}"] = ans

    if st.button("✅ 정답 확인 및 피드백"):
        score = 0
        total_mcq = sum(1 for q in data["quiz"] if q["options"])
        
        st.subheader("📊 채점 결과")
        for i, q in enumerate(data["quiz"]):
            # Streamlit의 key 기능을 활용해 저장된 값을 직접 가져옵니다.
            user_ans = st.session_state.get(f"q_{i}") 
            
            if q["options"]: # 객관식 채점
                correct_opt = q["options"][q["correct"]]
                if user_ans == correct_opt:
                    score += 1
                    st.success(f"Q{i+1}. 정답입니다! (선택: {user_ans})")
                else:
                    st.error(f"Q{i+1}. 오답입니다. (내 답: {user_ans} / 정답: {correct_opt})")
            else: # 주관식 피드백
                st.info(f"Q{i+1}. 주관식 작성 완료 (내 답: {user_ans})")

        st.divider()
        st.success(f"🎉 객관식 최종 점수: {score} / {total_mcq}")
        st.warning(f"💡 AI 학습 팁: {data.get('tips', '추가 복습이 필요합니다.')}")
