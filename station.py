import pandas as pd
import streamlit as st


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
