import pandas as pd
import matplotlib.pyplot as plt

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

# 2. 시간대별 혼잡도를 계산하는 함수 (전체 합계)
def cal_congestion(station):
    station_data = train_station[train_station['지하철역'] == station]
    time_columns = [col for col in train_station.columns if '승차인원' in col]
    time_data = station_data[time_columns].sum().reset_index()
    time_data.columns = ['시간대', '승차인원']
    time_data['시간대'] = time_data['시간대'].str.extract(r'(​?\d{2}시-\d{2}시)')
    return time_data

# 3. 출근시간대(07시-08시) 승차 데이터 추출
def peak_hour_analysis():
    train_station['07시-08시 승차인원'] = train_station['07시-08시 승차인원']
    peak_data = train_station.groupby('지하철역')['07시-08시 승차인원'].sum().reset_index()
    busiest_station = peak_data.loc[peak_data['07시-08시 승차인원'].idxmax()]
    return peak_data, busiest_station

# 4. 월별/연도별 승객 추이
def monthly_trend():
    monthly_data = train_station.groupby(['연도', '월']).sum().reset_index()
    monthly_data = monthly_data[['연도', '월'] + [col for col in train_station.columns if '승차인원' in col]]
    return monthly_data

# 결과 확인용 함수들 정의
def plot_congestion(station):
    import matplotlib.pyplot as plt
    station_data = cal_congestion(station)
    plt.figure(figsize=(12, 6))
    plt.bar(station_data['시간대'], station_data['승차인원'], color='skyblue')
    plt.title(f'{station} 시간대별 혼잡도', fontsize=16)
    plt.xlabel('시간대', fontsize=12)
    plt.ylabel('승차인원', fontsize=12)
    plt.xticks(rotation=45)
    plt.show()

def plot_monthly_trend():
    import matplotlib.pyplot as plt
    trend_data = monthly_trend()
    plt.figure(figsize=(12, 6))
    for year in trend_data['연도'].unique():
        yearly_data = trend_data[trend_data['연도'] == year]
        plt.plot(yearly_data['월'], yearly_data.iloc[:, 2:].sum(axis=1), label=f'{year}년')
    plt.title('월별 지하철 이용객 추이', fontsize=16)
    plt.xlabel('월', fontsize=12)
    plt.ylabel('이용객 수', fontsize=12)
    plt.legend()
    plt.show()

# 데이터 정제 완료 및 주요 함수 정의
"""
- 특정 승차역의 시간대별 혼잡도: plot_congestion('역 이름')
- 출근시간대 가장 붐비는 역 분석: peak_hour_analysis()
- 월별 이용객 추이 시각화: plot_monthly_trend()
"""

#plot_congestion('동대문')
#peak_hour_analysis()
#plot_monthly_trend()