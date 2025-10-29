import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta

# 🌟 페이지 설정
st.set_page_config(page_title="Study Guardian 💪", page_icon="📚", layout="wide")

# -------------------------------------------------------------------
# 🧠 초기 데이터 설정
if "points" not in st.session_state:
    st.session_state.points = 100  # 초기 포인트
if "study_log" not in st.session_state:
    st.session_state.study_log = []
if "friends" not in st.session_state:
    st.session_state.friends = {
        "민지": random.randint(40, 100),
        "현우": random.randint(40, 100),
        "지수": random.randint(40, 100)
    }

# -------------------------------------------------------------------
# 🎨 사이드바
st.sidebar.title("📖 Study Guardian")
menu = st.sidebar.radio(
    "메뉴 선택:",
    ["🏠 홈", "📅 계획 관리", "✅ 오늘의 체크", "🤖 AI 추천", "🎁 포인트 상점", "🏆 친구 경쟁", "📊 리포트"]
)

st.sidebar.markdown("---")
st.sidebar.info("💪 공부와 게임의 결합! \n\n당신만의 공부 관리 코치 🎯")

# -------------------------------------------------------------------
# 🏠 홈
if menu == "🏠 홈":
    st.markdown("## 💫 Study Guardian에 오신 것을 환영합니다!")
    st.write("오늘도 집중의 힘을 보여줄 준비 되셨나요? 🔥")

    name = st.text_input("이름을 입력하세요 ✍️", "홍길동")
    goal_type = st.selectbox("공부 목표 유형 선택:", ["내신", "정시", "둘 다"])
    exam_date = st.date_input("📅 시험일을 선택하세요", date.today() + timedelta(days=30))

    days_left = (exam_date - date.today()).days
    st.success(f"시험까지 남은 기간: {days_left}일 ⏰")

    st.markdown("### 🎯 오늘의 명언")
    quotes = [
        "🔥 '오늘의 한 걸음이 내일의 자신을 만든다.'",
        "💡 '꾸준함은 모든 재능을 이
