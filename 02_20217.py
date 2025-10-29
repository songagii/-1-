import streamlit as st
import pandas as pd
import random
from datetime import date, timedelta

# -------------------------------
# 🌟 기본 설정
st.set_page_config(page_title="Study Guardian 💪", page_icon="📚", layout="centered")

# -------------------------------
# 🧠 초기 상태 관리
if "points" not in st.session_state:
    st.session_state.points = 100
if "study_log" not in st.session_state:
    st.session_state.study_log = []
if "friends" not in st.session_state:
    st.session_state.friends = {
        "민지": random.randint(40, 100),
        "현우": random.randint(40, 100),
        "지수": random.randint(40, 100)
    }

# -------------------------------
# 🎨 사이드바 메뉴
st.sidebar.title("📘 Study Guardian")
menu = st.sidebar.radio(
    "메뉴 선택 👇",
    ["🏠 홈", "📅 계획 관리", "✅ 오늘의 체크", "🤖 AI 추천", "🎁 포인트 상점", "🏆 친구 경쟁", "📊 리포트"]
)
st.sidebar.markdown("---")
st.sidebar.info("AI 공부 조력자와 함께 성장하세요 ✨")

# -------------------------------
# 🏠 홈
if menu == "🏠 홈":
    st.title("💫 Study Guardian 💫")
    st.write("내신과 정시를 함께 관리하는 AI 공부 관리자 👩‍🏫")

    name = st.text_input("이름을 입력하세요 ✍️", "홍길동")
    exam_date = st.date_input("📅 시험일을 설정하세요", date.today() + timedelta(days=30))
    days_left = (exam_date - date.today()).days
    st.success(f"시험까지 {days_left}일 남았어요! ⏰")

    quotes = [
        "🔥 꾸준함이 곧 실력이다.",
        "💪 오늘의 한 걸음이 내일의 성적을 만든다.",
        "🌈 시작이 반이다. 지금 바로 시작하자!",
        "🚀 미래의 너가 오늘의 너에게 감사할 거야."
    ]
    st.info(random.choice(quotes))

# -------------------------------
# 📅 계획 관리
elif menu == "📅 계획 관리":
    st.header("📅 공부 계획 세우기")
    subject = st.text_input("공부 과목:", "수학")
    goal = st.text_input("공부 목표:", "기출문제 5개 풀기")
    if st.button("계획 추가"):
        st.session_state.study_log.append({"과목": subject, "목표": goal, "완료": False})
        st.success("계획이 추가되었습니다 🎯")

    if st.session_state.study_log:
        st.subheader("🗓️ 나의 계획 목록")
        df = pd.DataFrame(st.session_state.study_log)
        st.dataframe(df)

# -------------------------------
# ✅ 오늘의 체크
elif menu == "✅ 오늘의 체크":
    st.header("✅ 오늘의 공부 점검")
    if not st.session_state.study_log:
        st.warning("공부 계획을 먼저 추가해주세요 📋")
    else:
        for i, task in enumerate(st.session_state.study_log):
            done = st.checkbox(f"{task['과목']} - {task['목표']}", value=task["완료"], key=f"check_{i}")
            st.session_state.study_log[i]["완료"] = done
        if any(t["완료"] for t in st.session_state.study_log):
            st.session_state.points += 10
            st.success("💰 오늘의 포인트 +10!")

    st.info(f"현재 포인트: {st.session_state.points}P")

# -------------------------------
# 🤖 AI 추천 (간단 버전)
elif menu == "🤖 AI 추천":
    st.header("🤖 AI 공부 추천")
    mood = st.select_slider("오늘의 기분은?", ["😫 낮음", "🙂 보통", "🔥 최고"])
    focus_time = st.slider("오늘 집중 가능 시간 (시간)", 1, 10, 3)

    if st.button("AI 추천 받기"):
        if mood == "😫 낮음":
            rec = "오늘은 복습 위주로 가볍게! 🌷"
        elif mood == "🙂 보통":
            rec = "계획한 만큼 꾸준히! 💪"
        else:
            rec = "오늘은 어려운 과목에 도전해보세요! 🚀"
        st.success(f"✨ 추천: {rec}")
        st.info(f"추천 공부 시간: {focus_time}시간")

# -------------------------------
# 🎁 포인트 상점
elif menu == "🎁 포인트 상점":
    st.header("🎁 포인트 상점")
    st.info(f"현재 포인트: {st.session_state.points}P")

    items = {
        "🎧 집중 배경음": 50,
        "💎 응원 메시지 강화": 80,
        "🌈 캐릭터 꾸미기": 100
    }

    for item, cost in items.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{item} — {cost}P")
        with col2:
            if st.button(f"구매 {item}", key=item):
                if st.session_state.points >= cost:
                    st.session_state.points -= cost
                    st.success(f"{item} 구매 완료! 🎉")
                else:
                    st.error("포인트가 부족합니다 😭")

# -------------------------------
# 🏆 친구 경쟁
elif menu == "🏆 친구 경쟁":
    st.header("🏆 친구 경쟁 모드")

    # 친구 데이터 + 나의 점수
    my_score = random.randint(60, 100)
    df = pd.DataFrame({
        "이름": list(st.session_state.friends.keys()) + ["나"],
        "점수": list(st.session_state.friends.values()) + [my_score]
    }).sort_values("점수", ascending=False)

    st.bar_chart(df.set_index("이름"))
    st.dataframe(df)
    st.info("🔥 주간 1등은 보상 포인트 +30!")

# -------------------------------
# 📊 리포트
elif menu == "📊 리포트":
    st.header("📊 나의 공부 리포트")
    if not st.session_state.study_log:
        st.warning("아직 계획이 없습니다 😅")
    else:
        total = len(st.session_state.study_log)
        done = sum(1 for x in st.session_state.study_log if x["완료"])
        rate = done / total
        st.progress(rate)
        st.metric("✅ 달성률", f"{rate*100:.1f}%")
        st.metric("💰 포인트", f"{st.session_state.points}P")

        if rate == 1.0:
            st.balloons()
            st.success("완벽한 달성! 🎉 보너스 +50P")
            st.session_state.points += 50
