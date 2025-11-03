# streamlit_emergency_ob_app.py
# Streamlit 앱: 임산부 응급실 뺑뺑이 해결 프로토타입
# 기능 요약:
# 1) 사용자 위치(GPS 수동입력 또는 브라우저 요청) 기반 최적 병원 검색 및 경로(외부 라우팅 API 사용)
# 2) 병원 내부 대기/수용 상태(관리자 업데이트 가능) 표시 및 포화 시 자동 추천
# 3) 사후 피드백 저장 및 지역별 접근성 지표 생성
# 4) 다국어(한국어/영어/중국어) 안내(간단한 정적 번역 + 자리표시자: 외부 번역 API 연결 가능)
# 주의: 실제 배포시 보안(API 키, 인증), 개인정보보호(의료정보 취급) 규정 준수 필요

import streamlit as st
import pandas as pd
import sqlite3
import math
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime

# --------------- 설정 (사용자 편의에 맞게 수정) -----------------
ORS_API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"  # 경로(라우팅) API 키 (예: OpenRouteService)
ADMIN_PASSWORD = "admin123"  # 데모용 관리자 비밀번호 (실사용 시 안전하게 보관)
DB_PATH = "hospital_feedback.db"
HOSPITAL_CSV = "hospitals_sample.csv"  # 샘플 병원 데이터 파일 (없으면 앱이 생성)

# --------------- 유틸리티 함수 -----------------

def haversine(lat1, lon1, lat2, lon2):
    # km 단위
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT,
            rating INTEGER,
            comment TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()


# --------------- 병원 데이터 로드/초기화 -----------------

def create_sample_hospitals(path=HOSPITAL_CSV):
    sample = pd.DataFrame([
        {"id":"H001","name":"서울중앙여성병원","lat":37.5665,"lon":126.9780,
         "accepting":True,"waiting":2,"delivery_beds":1},
        {"id":"H002","name":"강남모성병원","lat":37.4979,"lon":127.0276,
         "accepting":True,"waiting":8,"delivery_beds":0},
        {"id":"H003","name":"동대문응급센터","lat":37.5796,"lon":127.0094,
         "accepting":False,"waiting":0,"delivery_beds":0},
        {"id":"H004","name":"성북모자병원","lat":37.5891,"lon":127.0164,
         "accepting":True,"waiting":1,"delivery_beds":2}
    ])
    sample.to_csv(path, index=False)
    return sample


def load_hospitals(path=HOSPITAL_CSV):
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        df = create_sample_hospitals(path)
    return df


# --------------- 병원 검색 및 추천 로직 -----------------

def find_nearest_hospitals(user_lat, user_lon, hospitals_df, top_n=5):
    df = hospitals_df.copy()
    df['distance_km'] = df.apply(lambda r: haversine(user_lat, user_lon, r['lat'], r['lon']), axis=1)
    # 가중치 정하기: 수용 여부>분만 가능 여부>대기
    def score_row(r):
        score = r['distance_km']
        if not r['accepting']:
            score += 1000
        # 분만 침대(0이면 페널티)
        if r['delivery_beds'] == 0:
            score += 20
        # 대기 인원이 많으면 가중치
        score += r['waiting'] * 2
        return score
    df['score'] = df.apply(score_row, axis=1)
    df = df.sort_values('score')
    return df.reset_index(drop=True)


# --------------- 라우팅 (외부 API 호출) -----------------

def get_route_ors(start_lat, start_lon, end_lat, end_lon, api_key=ORS_API_KEY):
    # OpenRouteService 예제 사용
    if not api_key or api_key == "YOUR_OPENROUTESERVICE_API_KEY":
        return None, "API_KEY_NOT_SET"
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    body = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}
    try:
        res = requests.post(url, json=body, headers=headers, timeout=5)
        res.raise_for_status()
        return res.json(), None
    except Exception as e:
        return None, str(e)


# --------------- 병원 상태 업데이트 (관리자용, 데모) -----------------

def update_hospital_status(hospitals_df, hid, accepting=None, waiting=None, delivery_beds=None, path=HOSPITAL_CSV):
    df = hospitals_df.copy()
    idx = df.index[df['id'] == hid]
    if len(idx) == 0:
        return False
    i = idx[0]
    if accepting is not None:
        df.at[i, 'accepting'] = accepting
    if waiting is not None:
        df.at[i, 'waiting'] = waiting
    if delivery_beds is not None:
        df.at[i, 'delivery_beds'] = delivery_beds
    df.to_csv(path, index=False)
    return True


# --------------- 피드백 저장 -----------------

def save_feedback(hospital_id, rating, comment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO feedback (hospital_id, rating, comment, timestamp) VALUES (?, ?, ?, ?)',
              (hospital_id, rating, comment, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_feedback_summary():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT hospital_id, AVG(rating) as avg_rating, COUNT(*) as cnt FROM feedback GROUP BY hospital_id', conn)
    conn.close()
    return df


# --------------- 간단 다국어 지원 -----------------

i18n = {
    'ko': {
        'title': '임산부 응급 병원 매칭 (프로토타입)',
        'enter_location': '사용자 위치 입력(위도,경도)',
        'detect_note': '*브라우저 위치 정보 사용이 불가능하면 수동으로 입력하세요.*',
        'find': '가까운 병원 찾기',
        'nearest': '추천 병원(거리/대기/수용 반영)',
        'route': '경로 보기(외부 라우팅 API 필요)',
        'call_119': '119로 연결',
        'call_hospital': '병원으로 전화',
        'admin_panel': '병원 상태 업데이트(관리자)',
        'feedback': '방문 후기/평점 남기기',
        'language': '언어'
    },
    'en': {
        'title': 'Emergency OB Hospital Matcher (Prototype)',
        'enter_location': 'Enter user location (lat, lon)',
        'detect_note': '*If browser geolocation is unavailable, enter manually.*',
        'find': 'Find nearby hospitals',
        'nearest': 'Recommended hospitals (distance/wait/availability)',
        'route': 'Show route (external routing API required)',
        'call_119': 'Call 119 (EMS)',
        'call_hospital': 'Call hospital',
        'admin_panel': 'Hospital status update (admin)',
        'feedback': 'Leave feedback/rating',
        'language': 'Language'
    },
    'zh': {
        'title': '孕产妇紧急医院匹配（原型）',
        'enter_location': '输入用户位置（纬度，经度）',
        'detect_note': '*如果无法使用浏览器定位，请手动输入。*',
        'find': '查找附近医院',
        'nearest': '推荐医院（距离/等候/可收治）',
        'route': '查看路线（需要外部路由API）',
        'call_119': '拨打119（急救）',
        'call_hospital': '拨打医院',
        'admin_panel': '医院状态更新（管理员）',
        'feedback': '留下反馈/评分',
        'language': '语言'
    }
}


# --------------- Streamlit UI -----------------

def main():
    st.set_page_config(layout='wide', page_title='임산부 응급 매칭')

    # 초기화
    init_db()
    hospitals_df = load_hospitals()

    # 언어 선택
    lang = st.sidebar.selectbox('Language / 언어', options=['ko', 'en', 'zh'], index=0)
    T = i18n[lang]

    st.title(T['title'])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"**{T['enter_location']}**")
        st.caption(T['detect_note'])
        user_lat = st.number_input('Latitude', format="%.6f", value=37.5665)
        user_lon = st.number_input('Longitude', format="%.6f", value=126.9780)
        top_n = st.slider('몇 개 병원을 볼까요?', 1, 10, 5)
        if st.button(T['find']):
            nearest = find_nearest_hospitals(user_lat, user_lon, hospitals_df, top_n)
            st.subheader(T['nearest'])
            st.dataframe(nearest[['id','name','distance_km','waiting','delivery_beds','accepting','score']])

            # 지도 표시
            m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
            folium.Marker([user_lat, user_lon], tooltip='You', icon=folium.Icon(color='blue')).add_to(m)
            mc = MarkerCluster().add_to(m)
            for _, r in nearest.iterrows():
                popup_html = f"<b>{r['name']}</b><br/>distance: {r['distance_km']:.2f} km<br/>waiting: {r['waiting']}<br/>delivery_beds: {int(r['delivery_beds'])}<br/>accepting: {r['accepting']}"
                folium.Marker([r['lat'], r['lon']], popup=popup_html).add_to(mc)

            st_data = st_folium(m, width=700, height=450)

            # 병원 선택 및 라우팅
            st.markdown('---')
            st.markdown('**선택 병원으로 경로 보기 / 호출 기능**')
            selected = st.selectbox('병원 선택', options=nearest['id'].tolist())
            sel_row = nearest[nearest['id'] == selected].iloc[0]
            st.write(f"선택: {sel_row['name']} (distance {sel_row['distance_km']:.2f} km)")

            if st.button(T['route']):
                route_json, error = get_route_ors(user_lat, user_lon, sel_row['lat'], sel_row['lon'])
                if route_json is None:
                    st.error(f"라우팅 실패: {error}. ORS API 키를 환경변수 또는 코드에 설정하세요.")
                else:
                    # 지도에 경로 그리기
                    m2 = folium.Map(location=[(user_lat+sel_row['lat'])/2, (user_lon+sel_row['lon'])/2], zoom_start=12)
                    folium.GeoJson(route_json, name='route').add_to(m2)
                    folium.Marker([user_lat, user_lon], tooltip='You', icon=folium.Icon(color='blue')).add_to(m2)
                    folium.Marker([sel_row['lat'], sel_row['lon']], tooltip=sel_row['name'], icon=folium.Icon(color='red')).add_to(m2)
                    st_folium(m2, width=700, height=450)

            # 119 호출 또는 병원 전화 (모바일에서 tel: 작동)
            st.markdown(f"[{T['call_119']}](tel:119)")
            st.markdown(f"[{T['call_hospital']}](tel:010-0000-0000) - 병원 번호는 실제 데이터와 연동 필요")

    with col2:
        st.subheader(T['feedback'])
        fb_hospital = st.text_input('병원 ID (예: H001)')
        fb_rating = st.slider('평점', 1, 5, 5)
        fb_comment = st.text_area('의견(선택)')
        if st.button('제출'):
            if fb_hospital:
                save_feedback(fb_hospital, fb_rating, fb_comment)
                st.success('후기 등록 감사합니다.')
            else:
                st.error('병원 ID를 입력하세요.')

        st.markdown('---')
        st.subheader('지역별 접근성(요약)')
        feedback_summary = get_feedback_summary()
        st.dataframe(feedback_summary)

        st.markdown('---')
        st.subheader(T['admin_panel'])
        pwd = st.text_input('관리자 비밀번호', type='password')
        if pwd == ADMIN_PASSWORD:
            st.success('관리자 기능 접근 승인됨')
            sel_hosp = st.selectbox('업데이트할 병원 선택', options=hospitals_df['id'].tolist())
            hosp_row = hospitals_df[hospitals_df['id']==sel_hosp].iloc[0]
            new_accepting = st.checkbox('수용중', value=bool(hosp_row['accepting']))
            new_waiting = st.number_input('대기 인원', min_value=0, value=int(hosp_row['waiting']))
            new_beds = st.number_input('분만 가능 침대 수', min_value=0, value=int(hosp_row['delivery_beds']))
            if st.button('업데이트'):
                ok = update_hospital_status(hospitals_df, sel_hosp, accepting=new_accepting, waiting=new_waiting, delivery_beds=new_beds)
                if ok:
                    st.success('업데이트 성공. 새로고침 후 반영됩니다.')
                else:
                    st.error('업데이트 실패')
        else:
            st.info('관리자 접근은 비밀번호 필요')

    # 하단: 데이터 다운로드 및 간단 정책 제안용 CSV 생성
    st.markdown('---')
    st.subheader('데이터 다운로드 / 정책 제안')
    if st.button('지역별 병원 취약성 분석 생성'):
        # 예: 병원당 평균 평점과 수용여부를 합쳐 간단 취약지표 생성
        hosp = load_hospitals()
        fb = get_feedback_summary()
        merged = hosp.merge(fb, left_on='id', right_on='hospital_id', how='left')
        merged['avg_rating'] = merged['avg_rating'].fillna(0)
        # 취약성 지표: 수용여부(0/1), 분만침대, 대기인원, 평균평점
        merged['vulnerability'] = merged.apply(lambda r: (0 if r['accepting'] else 1)*50 + max(0,5-r['avg_rating'])*5 + (0 if r['delivery_beds']>0 else 20) + r['waiting']*2, axis=1)
        st.dataframe(merged[['id','name','accepting','delivery_beds','waiting','avg_rating','vulnerability']])
        csv = merged.to_csv(index=False).encode('utf-8')
        st.download_button('CSV 다운로드', data=csv, file_name='hospital_vulnerability.csv', mime='text/csv')

    st.caption('데모용 앱입니다. 실제 배포 전 개인정보·의료정보 관련 법규 검토와 API 키 보안 조치를 반드시 적용하세요.')


if __name__ == '__main__':
    main()
