import pandas as pd
import requests
from folium import Map, Marker, PolyLine

NAVER_CLIENT_ID = 'lu1ik7sx5m'  # 네이버 API 클라이언트 ID
NAVER_CLIENT_SECRET = 'bqEQKxuUajwFy8R4XvE7oPf3sNVN8HV256Fhg5iG'  # 네이버 API 시크릿

# API 호출
def call_naver_api(url):
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }
    response = requests.get(url, headers=headers)
    return response.json()

# CSV 파일 euc-kr 인코딩하고 읽기
data = pd.read_csv("호선별역명좌표.csv", encoding='euc-kr')

# 출발지 및 도착지 위도, 경도 설정
def get_coordinates(selected_start_station, selected_end_station, current_lat=None, current_lon=None):
    if current_lat and current_lon:
        # 사용자가 원하는 좌표를 출발지로 입력
        try:
            start_lat = float(current_lat)
            start_lon = float(current_lon)
        except ValueError:
            raise ValueError("위도와 경도는 숫자로 입력해야 합니다.")
    else:
        # 역명을 경도, 위도
        start_info = data[data['역명'] == selected_start_station]
        if not start_info.empty:
            start_lat = start_info.iloc[0]['위도']
            start_lon = start_info.iloc[0]['경도']
        else:
            raise ValueError("출발 역명을 찾을 수 없습니다.")
    
    end_info = data[data['역명'] == selected_end_station]
    if not end_info.empty:
        end_lat = end_info.iloc[0]['위도']
        end_lon = end_info.iloc[0]['경도']
    else:
        raise ValueError("목적 역명을 찾을 수 없습니다.")
    
    return start_lat, start_lon, end_lat, end_lon

# 경로 탐색 및 지도 생성 함수
def generate_route_map(start_lat, start_lon, end_lat, end_lon):
    url = f"https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start={start_lon},{start_lat}&goal={end_lon},{end_lat}&option=traoptimal"
    route_info = call_naver_api(url)

    if 'route' in route_info:
        route_coords = [(path[1], path[0]) for path in route_info['route']['traoptimal'][0]['path']]
        
        # 지도 생성
        m = Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=13)
        Marker(location=[start_lat, start_lon], popup="출발지").add_to(m)
        Marker(location=[end_lat, end_lon], popup="목적지").add_to(m)
        PolyLine(route_coords, color="green", weight=4).add_to(m)
        return m
    else:
        raise ValueError("경로를 찾을 수 없습니다.")
