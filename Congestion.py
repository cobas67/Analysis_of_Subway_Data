import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 맑은 고딕 한글 폰트 설정
def set_font():
    font_path = 'C:\\Windows\\Fonts\\malgun.ttf'
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

# CSV 파일 불러온 후 ecu-kr 인코딩 읽기
def load_data():
    df = pd.read_csv('지하철혼잡도.csv', encoding='euc-kr')
    return df

# 혼잡도 계산 함수
def calculate_congestion(ride, alight, line):
    if line in ['1호선', '2호선', '3호선', '4호선', '5호선', '6호선', '7호선', '8호선', '9호선']:
        total_capacity = 16000  # 1~9호선 정원수
    elif line == '경춘선':
        total_capacity = 4800  # 경춘선 정원수
    else:
        total_capacity = 0
    
    total_passengers = ride + alight
    congestion_ratio = total_passengers / total_capacity * 100

    if congestion_ratio <= 79:
        congestion_level = '여유'
    elif 80 < congestion_ratio <= 129:
        congestion_level = '보통'
    else:
        congestion_level = '혼잡'
    
    return congestion_ratio, congestion_level

# 호선에 따른 지하철역 목록 반환 
def get_stations_by_line(df, line):
    # 호선에 해당하는 역 추출
    stations = df[df['호선명'] == line]['지하철역'].unique().tolist()
    return stations

def main():
    # 한글 폰트 설정
    set_font()

    # 데이터 불러오기
    df = load_data()

    # 호선 선택
    line = '경춘선'
    stations = get_stations_by_line(df, line)
    station = '춘천' 

    # 해당 호선과 역에 대한 데이터 필터링
    line_data = df[(df['호선명'] == line) & (df['지하철역'] == station)]

    # 시간대별 혼잡도 계산
    congestion_data = []
    time_slots = [
        "04시-05시", "05시-06시", "06시-07시", "07시-08시", "08시-09시", "09시-10시", "10시-11시",
        "11시-12시", "12시-13시", "13시-14시", "14시-15시", "15시-16시", "16시-17시", "17시-18시", 
        "18시-19시", "19시-20시", "20시-21시", "21시-22시", "22시-23시", "23시-24시", "00시-01시", 
        "01시-02시", "02시-03시", "03시-04시"
    ]

    for time_slot in time_slots:
        # 오전 2시 ~ 4시는 운행중지로 가정
        if time_slot in ["02시-03시", "03시-04시"]:
            congestion_data.append((time_slot, None, '운행 안함'))
            continue

        # 시간대별 승,하차 데이터 찾기
        ride_column = f"{time_slot} 승차인원"
        alight_column = f"{time_slot} 하차인원"
        
        if ride_column in line_data.columns and alight_column in line_data.columns:
            ride = line_data[ride_column].values[0]
            alight = line_data[alight_column].values[0]
            congestion_ratio, congestion_level = calculate_congestion(ride, alight, line)
            congestion_data.append((time_slot, congestion_ratio, congestion_level))
        else:
            congestion_data.append((time_slot, None, '데이터 없음'))

    # DataFrame 변환
    congestion_df = pd.DataFrame(congestion_data, columns=["시간대", "혼잡도 비율 (%)", "혼잡도 상태"])

    # "운행 안함"
    congestion_df['혼잡도 비율 (%)'] = pd.to_numeric(congestion_df['혼잡도 비율 (%)'], errors='coerce')

    # 혼잡도가 비율이 높은 시간대와 낮은 시간대 찾기
    min_congestion_row = congestion_df.loc[congestion_df['혼잡도 비율 (%)'].idxmin()]
    max_congestion_row = congestion_df.loc[congestion_df['혼잡도 비율 (%)'].idxmax()]

    min_congestion_time = min_congestion_row['시간대']
    max_congestion_time = max_congestion_row['시간대']
    min_congestion_value = min_congestion_row['혼잡도 비율 (%)']
    max_congestion_value = max_congestion_row['혼잡도 비율 (%)']

    # 혼잡도 출력
    print(f"{line} {station} 시간대별 혼잡도 비율")
    print(congestion_df)

    # 혼잡도 막대 그래프
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(congestion_df['시간대'], congestion_df['혼잡도 비율 (%)'], color='skyblue')
    ax.set_title(f"{line} {station} 시간대별 혼잡도 비율")
    ax.set_xlabel("시간대")
    ax.set_ylabel("혼잡도 비율 (%)")
    plt.xticks(rotation=45)
    plt.show()

    # 혼잡도 꺾은선 그래프
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(congestion_df['시간대'], congestion_df['혼잡도 비율 (%)'], marker='o', color='green', linestyle='-', label='혼잡도 비율')
    ax.set_title(f"{line} {station} 시간대별 혼잡도 비율 (꺾은선 그래프)")
    ax.set_xlabel("시간대")
    ax.set_ylabel("혼잡도 비율 (%)")
    ax.legend()
    plt.xticks(rotation=45)
    plt.show()

    # 혼잡도가 가장 높고 가장 낮은 시간대 출력
    print(f"{line} {station} 혼잡도 분석")
    print(f"혼잡도가 가장 낮은 시간대: {min_congestion_time} ({min_congestion_value:.2f}%)")
    print(f"혼잡도가 가장 높은 시간대: {max_congestion_time} ({max_congestion_value:.2f}%)")

if __name__ == "__main__":
    main()
