import pandas as pd
import streamlit as st
import folium
from folium import Marker, PolyLine
from streamlit_folium import folium_static
import os
from dotenv import load_dotenv
import requests

# 환경 변수 불러오기
load_dotenv()
REACT_APP_ID = os.getenv('REACT_APP_ID')
REACT_APP_SECRET = os.getenv('REACT_APP_SECRET')

# 데이터 로드 함수
@st.cache_data
def load_data(file_name, encoding="EUC-KR"):
    df = pd.read_csv(file_name, encoding=encoding)
    # '사용월'에서 '연도'와 '월' 컬럼 생성
    if '사용월' in df.columns:
        df['연도'] = df['사용월'] // 100  # '사용월'에서 연도 추출
        df['월'] = df['사용월'] % 100    # '사용월'에서 월 추출
    return df

# 승차 데이터 필터링 함수
def get_in_subway_data(df):
    in_subway = df.columns.tolist()[:3]
    for col in df.columns.tolist():
        if '승차' in col:
            in_subway.append(col)
    return df[in_subway]

# 하차 데이터 필터링 함수
def get_out_subway_data(df):
    out_subway = df.columns.tolist()[:3]
    for col in df.columns.tolist():
        if '하차' in col:
            out_subway.append(col)
    return df[out_subway]

# 출근시간대(07시-08시) 분석 함수
def peak_hour_analysis(df):
    peak_column = "07시-08시 승차인원"
    if peak_column not in df.columns:
        st.error(f"데이터에 '{peak_column}' 컬럼이 없습니다.")
        return pd.DataFrame()
    peak_data = df.groupby('지하철역')[peak_column].sum().reset_index()
    peak_data = peak_data.sort_values(by=peak_column, ascending=False)
    return peak_data

# 월별/연도별 승객 추이 분석 함수
def monthly_trend_analysis(df):
    monthly_data = df.groupby(['연도', '월']).sum().reset_index()
    monthly_data['이용객_합계'] = monthly_data[[col for col in df.columns if '승차인원' in col]].sum(axis=1)
    return monthly_data

# 혼잡도 계산 함수
def calculate_congestion(ride, alight, line):
    if line in ['1호선', '2호선', '3호선', '4호선', '5호선', '6호선', '7호선', '8호선', '9호선']:
        total_capacity = 16000
    elif line == '경춘선':
        total_capacity = 4800
    else:
        total_capacity = 0

    total_passengers = ride + alight
    congestion_ratio = total_passengers / total_capacity * 100

    if congestion_ratio <= 79:
        congestion_level = '여유'
    elif 80 <= congestion_ratio <= 129:
        congestion_level = '보통'
    else:
        congestion_level = '혼잡'

    return congestion_ratio, congestion_level

# 지도 API 호출
def call_naver_api(url):
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
    if 'route' in route_info:
        route_coords = [(path[1], path[0]) for path in route_info['route']['traoptimal'][0]['path']]
        m = folium.Map(location=[(start_lat + end_lat) / 2, (start_lon + end_lon) / 2], zoom_start=13)
        Marker(location=[start_lat, start_lon], popup="출발지").add_to(m)
        Marker(location=[end_lat, end_lon], popup="목적지").add_to(m)
        PolyLine(route_coords, color="green", weight=4).add_to(m)
        return m
    else:
        st.error("경로를 찾을 수 없습니다.")
        return None

# Streamlit UI 시작
st.title("지하철 데이터 분석")

# 데이터 로드
train_station = load_data('db_station.csv')
coordinates_data = load_data("호선별역명좌표.csv")

# 사이드바 메뉴
menu = st.sidebar.radio("기능 선택", ["승차/하차 나누어 보기", "출근시간대 역별 승차인원", "월/연도별 승객 추이", "경로 탐색", "혼잡도 분석"])

if menu == "승차/하차 나누어 보기":
    st.header("1. 승차/하차 나누어 보기")
    option = st.radio("데이터 선택", ("승차 데이터", "하차 데이터"))
    if option == "승차 데이터":
        in_data = get_in_subway_data(train_station)
        st.dataframe(in_data)
    elif option == "하차 데이터":
        out_data = get_out_subway_data(train_station)
        st.dataframe(out_data)

elif menu == "출근시간대 역별 승차인원":
    st.header("2. 출근시간대 역별 승차인원")
    peak_data = peak_hour_analysis(train_station)
    if not peak_data.empty:
        st.dataframe(peak_data)
        busiest_station = peak_data.iloc[0]
        st.write(f"가장 혼잡한 역: {busiest_station['지하철역']} ({busiest_station['07시-08시 승차인원']}명)")
    else:
        st.write("출근 시간대 데이터를 분석할 수 없습니다.")

elif menu == "월/연도별 승객 추이":
    st.header("3. 월/연도별 승객 추이")
    monthly_data = monthly_trend_analysis(train_station)
    if not monthly_data.empty:
        selected_year = st.selectbox("연도를 선택하세요", sorted(monthly_data['연도'].unique()))
        year_data = monthly_data[monthly_data['연도'] == selected_year]
        st.line_chart(year_data, x='월', y='이용객_합계')
    else:
        st.write("월별/연도별 데이터를 분석할 수 없습니다.")

elif menu == "경로 탐색":
    st.header("4. 경로 탐색")
    start_station = st.selectbox("출발지를 선택하세요", coordinates_data['역명'].unique())
    end_station = st.selectbox("목적지를 선택하세요", coordinates_data['역명'].unique())
    if st.button("경로 시각화"):
        start_info = coordinates_data[coordinates_data['역명'] == start_station].iloc[0]
        end_info = coordinates_data[coordinates_data['역명'] == end_station].iloc[0]
        start_lat, start_lon = start_info['위도'], start_info['경도']
        end_lat, end_lon = end_info['위도'], end_info['경도']
        map_ = generate_route_map(start_lat, start_lon, end_lat, end_lon)
        if map_:
            folium_static(map_)

elif menu == "혼잡도 분석":
    st.header("5. 혼잡도 분석")
    selected_line = st.selectbox("호선을 선택하세요", train_station['호선명'].unique(), key="line_select")
    selected_station = st.selectbox("지하철역을 선택하세요", train_station[train_station['호선명'] == selected_line]['지하철역'].unique(), key="station_select")
    line_data = train_station[(train_station['호선명'] == selected_line) & (train_station['지하철역'] == selected_station)]
    congestion_data = []
    time_slots = [f"{hour:02d}시-{hour+1:02d}시" for hour in range(4, 24)] + ["00시-01시", "01시-02시"]
    for time_slot in time_slots:
        ride_col = f"{time_slot} 승차인원"
        alight_col = f"{time_slot} 하차인원"
        if ride_col in line_data.columns and alight_col in line_data.columns:
            ride = line_data[ride_col].values[0]
            alight = line_data[alight_col].values[0]
            ratio, level = calculate_congestion(ride, alight, selected_line)
            congestion_data.append((time_slot, ratio, level))
        else:
            congestion_data.append((time_slot, None, "데이터 없음"))
    congestion_df = pd.DataFrame(congestion_data, columns=["시간대", "혼잡도 비율 (%)", "혼잡도 상태"])
    st.dataframe(congestion_df)
