# Analysis_of_Subway_Data :mag_right:

- 6조
    - 20205165 박근혁
    - 20206602 강석훈
    - 20233236 이민영
    - 20195127 김세중 

## 프로젝트 개요 :station:
- 이 프로젝트는 서울 지하철 호선별 역별 시간대별 승하차 인원정보에 대한 데이터 자료 분석을 진행합니다.

- 서울은 대한민국의 수도권 지역으로 인구 집중포화현상이 일어나고 있으며 이에따라 유동인구도 많습니다. 매일 수백만 명의 승객들이 1~9호선을 탑승하며 다른 지역으로 이동하는데, 전철이 수용할 수 있는 승객수는 한정되어 있기때문에 승객이 몰리게 되며 이 과정에서 많은 승객들이 불편함이나, 사고위험에 노출되어 있습니다. 

- 저희는 분석한 데이터를 바탕으로 승객들에게 유의미한 정보를 제공하는 것이 목적이며 이를 통해 효율적인 시간관리와 최적화된 경로를 제공할 수 있도록 도와줍니다. 

## 설치방법
#### 1. Analysis_of_Subway_Data 리포지토리 포크

#### 2. 임의의 파일에서 vs코드를 열어 클론하기
```
git clone <포크한 자신의 리포지트리 URL>
```
#### 3. 가상환경 설치 및 requirements.txt파일 설치
```
python -m venv venv  # 가상환경 생성
venv\Scripts\activate  # 가상환경 활성화
pip install -r requirements.txt # 라이브러리 파일 설치
```

## 사용방법
```
venv\Scripts\activate # 가상환경 활성화
streamlit run station.py # 파이썬 실행창에 입력하면 streamlit이 실행되어 원하는 기능 사용가능 (지도 API는 네이버지도 API를 별도로 발급해서 파이썬 코드에 넣어주세요)
```
## 주요 기능 

- 사용월, 호선별, 역명, 시간대별로 승차, 하차 데이터를 나누어 볼 수 있는 기능
- 출근시간대 승차역 분석하는 기능
- 월/연도별 승객 추이 분석 기능
- 승차역, 하차역을 선택하면 경로를 탐색하는 네비게이션 기능
- 호선, 역별, 시간대별 혼잡도 분석기능
