import streamlit as st

# 🌈 페이지 설정
st.set_page_config(
    page_title="MBTI 직업 추천 💼",
    page_icon="💫",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 🎉 제목 영역
st.markdown(
    """
    <div style='text-align:center;'>
        <h1 style='font-size:60px;'>💫 MBTI 기반 직업 추천기 💫</h1>
        <p style='font-size:20px; color:#ff69b4;'>당신의 성격 유형으로 알아보는 완벽한 커리어 매칭 💼</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 🦄 MBTI 리스트
mbti_list = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

# 🎯 MBTI 선택
st.markdown("### 🌸 당신의 MBTI를 선택해주세요!")
selected_mbti = st.selectbox("👇 MBTI 선택", mbti_list)

# 💡 MBTI별 직업 추천 딕셔너리
career_dict = {
    "INTJ": "💻 데이터 과학자, AI 연구원, 전략 컨설턴트",
    "INTP": "🧠 연구원, 개발자, UX 디자이너",
    "ENTJ": "🏢 경영자, 프로젝트 매니저, 비즈니스 리더",
    "ENTP": "🚀 창업가, 마케팅 기획자, 크리에이티브 디렉터",
    "INFJ": "🎨 심리상담사, 작가, 사회운동가",
    "INFP": "🕊️ 예술가, 시인, 교육자",
    "ENFJ": "🌈 리더십 코치, 강사, 커뮤니케이션 전문가",
    "ENFP": "🔥 콘텐츠 크리에이터, 마케터, 이벤트 플래너",
    "ISTJ": "📊 회계사, 공무원, 품질관리자",
    "ISFJ": "💗 간호사, 교사, 사회복지사",
    "ESTJ": "🏗️ 관리자, 은행원, 운영 책임자",
    "ESFJ": "🤝 HR매니저, 서비스 기획자, 상담사",
    "ISTP": "🔧 엔지니어, 메카닉, 파일럿",
    "ISFP": "🎭 디자이너, 사진작가, 플로리스트",
    "ESTP": "💼 세일즈 전문가, 스포츠 코치, 트레이더",
    "ESFP": "🎤 연예인, 이벤트 MC, 뷰티 크리에이터",
}

# 🌟 결과 출력
if selected_mbti:
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align:center;'>
            <h2 style='font-size:45px;'>✨ {selected_mbti} ✨</h2>
            <p style='font-size:25px; color:#ffa500;'>당신에게 어울리는 직업은...</p>
            <h3 style='font-size:35px; color:#00bfff;'>{career_dict[selected_mbti]}</h3>
            <p style='font-size:20px; color:#808080;'>💬 당신의 성격은 세상을 빛나게 합니다 💖</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# 🌟 사이드바
st.sidebar.markdown("## 🌟 MBTI 직업 추천 가이드")
st.sidebar.info("자신의 MBTI를 선택하면 💼 어울리는 직업을 추천해드려요!\n\n🎯 꿈을 향한 여정을 시작해보세요 ✨")
st.sidebar.markdown("Made with ❤️ by **ChatGPT**")

# 🌈 푸터
st.markdown(
    """
    <div style='text-align:center; color:gray; margin-top:50px;'>
        🌸 <b>MBTI Career Finder</b> | Created with Streamlit 💕
    </div>
    """,
    unsafe_allow_html=True
)
