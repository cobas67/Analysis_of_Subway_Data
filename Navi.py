import streamlit as st
import folium
from folium import Marker, PolyLine
from streamlit_folium import folium_static
import pandas as pd
import os
import requests

# API 키 .evn파일에서 가져오기
REACT_APP_ID = os.environ.get('REACT_APP_ID')
REACT_APP_SECRET = os.environ.get('REACT_APP_SECRET')

# API 호출 함수
def call_naver_api(url):
    if not REACT_APP_ID or not REACT_APP_SECRET:
        st.error("Naver API 키가 설정되지 않았습니다. 환경변수를 확인해주세요.")
        return None

    headers = {
        "X-NCP-APIGW-API-KEY-ID": REACT_APP_ID,
        "X-NCP-APIGW-API-KEY": REACT_APP_SECRET
    }
    response = requests.get(url, headers=headers)
    return response.json()

# 지도 생성 함수
def generate_route_map(start_lat, start_lon, end_lat, end_lon):
    url = f"https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start={start_lon},{start_lat}&goal={end_lon},{end_lat}&option=traoptimal"
    route_info = call_naver_api(url)
    
    if not route_info or 'route' not in route_info:
        st.error("경로를 찾을 수 없습니다.")
        return None, None, None

    route_coords = [(path[1], path[0]) for path in route_info['route']['traoptimal'][0]['path']]
    
    # 여행 시간
    total_time = route_info['route']['traoptimal'][0]['summary']['duration'] / 60000  # 밀리초를 분으로 변환
    total_distance = route_info['route']['traoptimal'][0]['summary']['distance'] / 1000  # 미터를 킬로미터로 변환
    
    # 지도 생성
    m = folium.Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=13)
    Marker(location=[start_lat, start_lon], popup="출발지").add_to(m)
    Marker(location=[end_lat, end_lon], popup="목적지").add_to(m)
    PolyLine(route_coords, color="green", weight=4).add_to(m)
    
    return m, int(total_time), round(total_distance, 2)

# Streamlit
def main():
    st.title("경로 검색")

    # 좌표 데이터 로드
    coordinates_data = pd.read_csv("호선별역명좌표.csv", encoding="EUC-KR")

    # 출발지 입력 방식 선택
    input_type = st.radio("출발지 입력 방식 선택", ["역 선택", "좌표 직접 입력"])

    if input_type == "역 선택":
        # 출발지와 목적지 선택
        start_station = st.selectbox("출발지를 선택하세요", coordinates_data['역명'].unique())
        start_lat = coordinates_data[coordinates_data['역명'] == start_station]['위도'].values[0]
        start_lon = coordinates_data[coordinates_data['역명'] == start_station]['경도'].values[0]

        end_station = st.selectbox("목적지를 선택하세요", coordinates_data['역명'].unique())
        end_info = coordinates_data[coordinates_data['역명'] == end_station].iloc[0]
        end_lat, end_lon = end_info['위도'], end_info['경도']

    else:  # 좌표 직접 입력
        col1, col2 = st.columns(2)
        with col1:
            start_lat = st.number_input("출발지 위도 입력", format="%.6f", value=37.5665)
        with col2:
            start_lon = st.number_input("출발지 경도 입력", format="%.6f", value=126.9780)
        
        start_station = "사용자 지정 위치"

        # 목적지 입력
        end_station = st.selectbox("가까운 역을 선택하세요", coordinates_data['역명'].unique())
        end_info = coordinates_data[coordinates_data['역명'] == end_station].iloc[0]
        end_lat, end_lon = end_info['위도'], end_info['경도']

    # 경로 탐색
    if st.button("경로 탐색"):
        # 경로 지도 생성
        route_map, travel_time, total_distance = generate_route_map(start_lat, start_lon, end_lat, end_lon)
        
        if route_map:
            # 경로 정보 표시
            st.write(f"출발지: {start_station} (위도: {start_lat}, 경도: {start_lon})")
            st.write(f"도착지: {end_station}")
            
            # 예상 소요 시간 강조 및 글씨 크기 키우기
            st.markdown(f"**<span style='font-size:20px;'>🕒 예상 소요 시간: {travel_time}분</span>**", unsafe_allow_html=True)
            st.write(f"📏 총 거리: {total_distance}km")
            
            # 지도 표시
            folium_static(route_map)

if __name__ == "__main__":
    main()
