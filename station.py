import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv
import requests
import folium
from folium import Marker, PolyLine

train_station=pd.read_csv('db_station.csv', encoding='EUC-KR')
train_station=train_station.drop(columns=['작업일자'])

# 승차 관련 컬럼만 필터링
in_subway= train_station.columns.tolist()[:3]
for a in train_station.columns.tolist():
    if a.find('승차')!= -1 :
        in_subway.append(a)
in_subway_df = train_station[in_subway]

# 하차 관련 컬럼만 필터링
out_subway= train_station.columns.tolist()[:3]
for a in train_station.columns.tolist():
    if a.find('하차')!= -1 :
        out_subway.append(a)
out_subway_df = train_station[out_subway]

# 호선별
in_station_group=in_subway_df.groupby(['호선명','지하철역']).sum()
in_station_group=in_station_group.drop(['사용월'],axis=1)
out_station_group=out_subway_df.groupby(['호선명','지하철역']).sum()
out_station_group=out_station_group.drop(['사용월'],axis=1)

# 1. 날짜 정보 분리 및 추가
train_station['연도'] = train_station['사용월'] // 100
train_station['월'] = train_station['사용월'] % 100

# 시간대별 혼잡도 계산 함수
def cal_congestion(station):
    station_data = train_station[train_station['지하철역'] == station]
    time_columns = [col for col in train_station.columns if '승차인원' in col]
    time_data = station_data[time_columns].sum().reset_index()
    time_data.columns = ['시간대', '승차인원']
    time_data['시간대'] = time_data['시간대'].str.extract(r'(\d{2}시-\d{2}시)')
    return time_data

# 출근시간대(07시-08시) 분석 함수
def peak_hour_analysis():
    peak_data = train_station.groupby('지하철역')['07시-08시 승차인원'].sum().reset_index()
    peak_data = peak_data.sort_values(by='07시-08시 승차인원', ascending=False)
    busiest_station = peak_data.iloc[0]
    return peak_data, busiest_station

# 월별/연도별 승객 추이 분석 함수
def monthly_trend():
    monthly_data = train_station.groupby(['연도', '월']).sum().reset_index()
    monthly_data['이용객_합계'] = monthly_data[[col for col in monthly_data.columns if '승차인원' in col]].sum(axis=1)
    return monthly_data

# CSV 파일 불려와서 인코딩 
def load_data():
    df = pd.read_csv('db_station.csv', encoding='EUC-KR')
    return df

# 혼잡도 계산하지 위한 함수로 1~9호선 정원인원 16000명, 경춘선, 4800명으로 보고 승하차 더한값을 정원인원으로 나누기
def calculate_congestion(ride, alight, line):
    if line in ['1호선', '2호선', '3호선', '4호선', '5호선', '6호선', '7호선', '8호선', '9호선']:
        total_capacity = 16000
    elif line == '경춘선':
        total_capacity = 4800
    else:
        total_capacity = 0
    
    total_passengers = ride + alight
    congestion_ratio = total_passengers / total_capacity * 100
# 정원인원의 79% 이하면 여유, 129%이하면 보통 그외 혼잡
    if congestion_ratio <= 79:
        congestion_level = '여유'
    elif 80 < congestion_ratio <= 129:
        congestion_level = '보통'
    else:
        congestion_level = '혼잡'
    
    return congestion_ratio, congestion_level

# 호선 > 지하철역 목록 반환할 수 있게 함는 함수 
def get_stations_by_line(df, line):
    stations = df[df['호선명'] == line]['지하철역'].unique().tolist()
    return stations

def main():
    df = load_data()

    # 호선, 역 선택
    line = '경춘선' 
    stations = get_stations_by_line(df, line)
    station = '춘천' 

    # 선택에 대한 필터링 
    line_data = df[(df['호선명'] == line) & (df['지하철역'] == station)]

    # 시간대별로 혼잡도 표시
    congestion_data = []
    time_slots = [
        "04시-05시", "05시-06시", "06시-07시", "07시-08시", "08시-09시", "09시-10시", "10시-11시",
        "11시-12시", "12시-13시", "13시-14시", "14시-15시", "15시-16시", "16시-17시", "17시-18시", 
        "18시-19시", "19시-20시", "20시-21시", "21시-22시", "22시-23시", "23시-24시", "00시-01시", 
        "01시-02시", "02시-03시", "03시-04시"
    ]

    for time_slot in time_slots:
        # 오전 2시 ~ 4시 운행x
        if time_slot in ["02시-03시", "03시-04시"]:
            congestion_data.append((time_slot, None, '운행 안함'))
            continue

        # 시간대 승하차인원 데이터 검색
        ride_column = f"{time_slot} 승차인원"
        alight_column = f"{time_slot} 하차인원"
        
        if ride_column in line_data.columns and alight_column in line_data.columns:
            ride = line_data[ride_column].values[0]
            alight = line_data[alight_column].values[0]
            congestion_ratio, congestion_level = calculate_congestion(ride, alight, line)
            congestion_data.append((time_slot, congestion_ratio, congestion_level))
        else:
            congestion_data.append((time_slot, None, '데이터 없음'))

    
    congestion_df = pd.DataFrame(congestion_data, columns=["시간대", "혼잡도 비율 (%)", "혼잡도 상태"])

    # 운행 안함
    congestion_df['혼잡도 비율 (%)'] = pd.to_numeric(congestion_df['혼잡도 비율 (%)'], errors='coerce')

    # 가장 혼잡도가 높은 시간대와 낮은 시간대 찾기
    min_congestion_row = congestion_df.loc[congestion_df['혼잡도 비율 (%)'].idxmin()]
    max_congestion_row = congestion_df.loc[congestion_df['혼잡도 비율 (%)'].idxmax()]

    min_congestion_time = min_congestion_row['시간대']
    max_congestion_time = max_congestion_row['시간대']
    min_congestion_value = min_congestion_row['혼잡도 비율 (%)']
    max_congestion_value = max_congestion_row['혼잡도 비율 (%)']

    # 출력
    print(f"{line} {station} 시간대별 혼잡도 비율")
    print(congestion_df)

    # 최대 혼잡도와 낮은 혼잡도 출력
    print(f"{line} {station} 혼잡도 분석")
    print(f"혼잡도가 가장 낮은 시간대: {min_congestion_time} ({min_congestion_value:.2f}%)")
    print(f"혼잡도가 가장 높은 시간대: {max_congestion_time} ({max_congestion_value:.2f}%)")

if __name__ == "__main__":
    main()

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 네이버 API  불러오기
REACT_APP_ID = os.getenv('REACT_APP_ID')
REACT_APP_SECRET = os.getenv('REACT_APP_SECRET')

# API 호출
def call_naver_api(url):
    headers = {
        "X-NCP-APIGW-API-KEY-ID": REACT_APP_ID,  # REACT_APP_ID 사용
        "X-NCP-APIGW-API-KEY": REACT_APP_SECRET   # REACT_APP_SECRET 사용
    }
    response = requests.get(url, headers=headers)
    return response.json()

# CSV 파일 인코딩하고 읽기
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
        # 역명을 경도, 위도로 변환
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

# 경로 탐색 및 지도 생성 하기 위한 url
def generate_route_map(start_lat, start_lon, end_lat, end_lon):
    url = f"https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving?start={start_lon},{start_lat}&goal={end_lon},{end_lat}&option=traoptimal"
    route_info = call_naver_api(url)

    if 'route' in route_info:
        route_coords = [(path[1], path[0]) for path in route_info['route']['traoptimal'][0]['path']]
        
        # 지도를 생성하게 해주는 함수
        m = folium.Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=13)
        Marker(location=[start_lat, start_lon], popup="출발지").add_to(m)
        Marker(location=[end_lat, end_lon], popup="목적지").add_to(m)
        PolyLine(route_coords, color="green", weight=4).add_to(m)
        return m
    else:
        raise ValueError("경로를 찾을 수 없습니다.")