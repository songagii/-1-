import io
import math
import pandas as pd
import streamlit as st
import pydeck as pdk
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="🚑 실시간 내 주변 응급실 찾기", layout="wide")
st.title("🚑 실시간 내 주변 응급실 찾기 (CSV + GPS)")

# ----------------------------
# 유틸
# ----------------------------
def calc_distance(lat1, lon1, lat2, lon2):
    """하버사인 공식으로 거리(km) 계산"""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def coerce_float(series):
    """문자열 좌표를 안전하게 float로 변환"""
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.strip(), errors="coerce")

def guess_columns(df):
    """CSV마다 다른 컬럼명을 자동 매핑 (병원위도/병원경도 추가됨)"""
    def pick(cands):
        for c in cands:
            if c in df.columns:
                return c
        return None
    return {
        "lat":  pick(["lat", "위도", "병원위도", "Latitude", "latitude", "Y", "y"]),
        "lon":  pick(["lon", "경도", "병원경도", "Longitude", "longitude", "X", "x"]),
        "name": pick(["name", "병원명", "기관명", "기관명(국문)", "요양기관명"]),
        "tel":  pick(["tel", "전화", "전화번호", "대표전화", "응급전화", "응급실전화"]),
        "addr": pick(["addr", "주소", "도로명주소", "지번주소"]),
    }

def tel_link(t):
    if pd.isna(t) or str(t).strip() == "":
        return ""
    return f"[전화](tel:{str(t).strip()})"

def naver_maps_link(lat, lon, name):
    return f"[길찾기](https://map.naver.com/v5/directions/-/-/{lon},{lat},{name})"

# ----------------------------
# 1) CSV 업로드 (인코딩 자동 감지)
# ----------------------------
uploaded_file = st.file_uploader("📂 병원 위치 CSV 업로드 (위도/경도 또는 병원위도/병원경도 포함)", type=["csv"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    hospitals = None
    for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin1"):
        try:
            hospitals = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
            st.caption(f"✅ CSV 인코딩 자동 감지 성공: {enc}")
            break
        except UnicodeDecodeError:
            continue
    if hospitals is None:
        st.error("❌ CSV 인코딩을 읽지 못했습니다. (UTF-8/CP949/EUC-KR/LATIN1 시도 실패)")
        st.stop()

    st.success("✅ 병원 데이터 불러오기 성공!")
    st.dataframe(hospitals.head(), use_container_width=True)

    # 2) 컬럼 자동 인식 + 좌표 정리
    colmap = guess_columns(hospitals)
    if not colmap["lat"] or not colmap["lon"]:
        st.error("위도/경도 컬럼을 찾지 못했습니다. CSV에 'lat/lon' 또는 '위도/경도' 혹은 '병원위도/병원경도' 컬럼이 필요해요.")
        st.stop()

    hospitals = hospitals.rename(columns={
        colmap["lat"]: "lat",
        colmap["lon"]: "lon",
        **({colmap["name"]: "name"} if colmap["name"] else {}),
        **({colmap["tel"]: "tel"} if colmap["tel"] else {}),
        **({colmap["addr"]: "addr"} if colmap["addr"] else {}),
    })
    hospitals["lat"] = coerce_float(hospitals["lat"])
    hospitals["lon"] = coerce_float(hospitals["lon"])
    hospitals = hospitals.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    # 3) GPS / 수동 입력
    st.markdown("### 📍 현재 위치 설정")
    if "user_lat" not in st.session_state:
        st.session_state.user_lat = None
        st.session_state.user_lon = None

    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        if st.button("현재 위치 가져오기 (브라우저 GPS)"):
            loc = get_geolocation()
            if loc and isinstance(loc, dict) and "coords" in loc:
                st.session_state.user_lat = float(loc["coords"]["latitude"])
                st.session_state.user_lon = float(loc["coords"]["longitude"])
    with c2:
        st.session_state.user_lat = st.number_input(
            "위도", value=st.session_state.user_lat if st.session_state.user_lat else 37.5665, format="%.6f"
        )
    with c3:
        st.session_state.user_lon = st.number_input(
            "경도", value=st.session_state.user_lon if st.session_state.user_lon else 126.9780, format="%.6f"
        )
    with c4:
        radius_km = st.slider("탐색 반경(km)", 2, 30, 10)

    user_lat = float(st.session_state.user_lat)
    user_lon = float(st.session_state.user_lon)

    # 4) 거리 계산 + 필터링
    hospitals["distance_km"] = hospitals.apply(
        lambda r: calc_distance(user_lat, user_lon, float(r["lat"]), float(r["lon"])),
        axis=1
    )
    result = hospitals[hospitals["distance_km"] <= radius_km].copy()
    if "tel" in result.columns:
        result["전화"] = result["tel"].apply(tel_link)
    else:
        result["전화"] = ""
    result["길찾기"] = result.apply(lambda r: naver_maps_link(r["lat"], r["lon"], str(r.get("name", "병원"))), axis=1)
    result = result.sort_values(["distance_km"]).reset_index(drop=True)

    # 5) 표 출력
    st.markdown("### 🏥 가까운 병원 목록")
    view_cols = [c for c in ["name","addr","tel","distance_km","전화","길찾기","lat","lon"] if c in result.columns]
    st.dataframe(result[view_cols].head(80), use_container_width=True)

    # 6) 지도 시각화
    st.markdown("### 🗺️ 지도 보기")
    layers = []
    hospital_layer = pdk.Layer(
        "ScatterplotLayer",
        data=result,
        get_position="[lon, lat]",
        get_radius=80,
        pickable=True,
        radius_min_pixels=4,
        radius_max_pixels=24,
        auto_highlight=True,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=result.head(30),
        get_position="[lon, lat]",
        get_text="name" if "name" in result.columns else "'병원'",
        get_size=12,
        get_alignment_baseline="'bottom'",
    )
    me_df = pd.DataFrame([{"lon": user_lon, "lat": user_lat, "name": "내 위치"}])
    me_dot = pdk.Layer("ScatterplotLayer", data=me_df, get_position="[lon, lat]", get_radius=120, pickable=False)
    me_halo = pdk.Layer("ScatterplotLayer", data=me_df, get_position="[lon, lat]", get_radius=300, pickable=False, opacity=0.15)
    layers += [hospital_layer, text_layer, me_dot, me_halo]

    center_lat, center_lon = (user_lat, user_lon)
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12)
    tooltip = {"html": "<b>{name}</b><br/>{addr}<br/>거리: {distance_km}km<br/>{tel}", "style": {"backgroundColor": "white", "color": "black"}}

    deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip=tooltip, map_style=None)
    st.pydeck_chart(deck, use_container_width=True)

else:
    st.info("CSV를 업로드하면 병원 목록을 보여드릴게요. (lat/lon 또는 위도/경도/병원위도/병원경도 컬럼 필수)")
