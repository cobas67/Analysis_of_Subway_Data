import pandas as pd
import streamlit as st
import folium
from folium import Marker, PolyLine
from streamlit_folium import folium_static
import os
from dotenv import load_dotenv
import requests

# 환경 변수 로드
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

        st.dataframe(in_data, use_container_width=400, height=300)
    elif option == "하차 데이터":
        out_data = get_out_subway_data(train_station)
        st.dataframe(out_data, use_container_width=400, height=300)


elif menu == "출근시간대 역별 승차인원":
    st.header("2. 출근시간대 역별 승차인원")
    peak_data = peak_hour_analysis(train_station)
    if not peak_data.empty:

        st.dataframe(peak_data, use_container_width=400, height=200)
        busiest_station = peak_data.iloc[0]
        st.write(f"가장 혼잡한 역: **{busiest_station['지하철역']}** ({busiest_station['07시-08시 승차인원']}명)")
        # 경고 문구 추가
        st.warning(f"⚠️ '{busiest_station['지하철역']}' 역은 출근 시간대에 매우 혼잡합니다. 가능하다면 다른 경로를 고려하세요!")
        # 특정 역 혼잡도 확인 기능
        user_input = st.text_input("혼잡도를 확인할 역 이름을 입력하세요:")
        if user_input:
            station_data = peak_data[peak_data['지하철역'] == user_input]
            if not station_data.empty:
                count = station_data.iloc[0]['07시-08시 승차인원']
                st.write(f"**{user_input}** 역의 07시-08시 승차인원은 {count}명입니다.")
                if count == busiest_station['07시-08시 승차인원']:
                    st.warning(f"⚠️ '{user_input}' 역은 가장 혼잡한 역 중 하나입니다. 다른 경로를 고려하세요!")
                else:
                    st.info(f"'{user_input}' 역은 상대적으로 혼잡하지 않습니다.")
            else:
                st.error(f"'{user_input}' 역에 대한 데이터가 없습니다.")

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

elif menu == "혼잡도 분석":
    st.header("5. 혼잡도 분석")
    
    # 사용자 입력
    selected_line = st.selectbox("호선을 선택하세요", train_station['호선명'].unique(), key="line_select")
    selected_station = st.selectbox("지하철역을 선택하세요", train_station[train_station['호선명'] == selected_line]['지하철역'].unique(), key="station_select")
    
    # 데이터 필터링
    line_data = train_station[(train_station['호선명'] == selected_line) & (train_station['지하철역'] == selected_station)]
    
    # 혼잡도 데이터 계산

    congestion_data = []
    time_slots = [f"{hour:02d}시-{hour+1:02d}시" for hour in range(4, 24)] + ["00시-01시", "01시-02시"]
    for time_slot in time_slots:
        ride_col = f"{time_slot} 승차인원"
        alight_col = f"{time_slot} 하차인원"
        if ride_col in line_data.columns and alight_col in line_data.columns:
            ride = line_data[ride_col].values[0]
            alight = line_data[alight_col].values[0]
            ratio, level = calculate_congestion(ride, alight, selected_line)

            congestion_data.append({"시간대": time_slot, "혼잡도 비율 (%)": ratio, "혼잡도 상태": level})
        else:
            congestion_data.append({"시간대": time_slot, "혼잡도 비율 (%)": None, "혼잡도 상태": "데이터 없음"})
    
    # 데이터프레임 생성
    congestion_df = pd.DataFrame(congestion_data)
    
    # 혼잡도 데이터 중 숫자가 있는 부분만 필터링
    valid_data = congestion_df[congestion_df["혼잡도 비율 (%)"].notnull()]
    
    # 시간대별 혼잡도 비율 시각화 (st.bar_chart)
    st.subheader(f"{selected_station} 역의 시간대별 혼잡도")
    if not valid_data.empty:
        chart_data = valid_data.set_index("시간대")[["혼잡도 비율 (%)"]]
        st.bar_chart(chart_data)

        # 혼잡도가 300이 넘는 시간대 경고 메시지 추가
        very_congested_times = valid_data[valid_data["혼잡도 비율 (%)"] > 300]["시간대"].tolist()
        if very_congested_times:
            st.error(f"🚨 '{selected_station}' 역은 다음 시간대에 혼잡도가 300을 초과합니다: {',  '.join(very_congested_times)}. 꼭 피해 주세요!")
    else:
        st.error("유효한 혼잡도 데이터가 없습니다.")

