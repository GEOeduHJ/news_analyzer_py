# 한국 뉴스 데이터 분석 대시보드

이 프로젝트는 한국 뉴스 데이터를 분석하는 Streamlit 기반 대시보드입니다. 뉴스 기사의 키워드, 기관, 연도별 트렌드 등을 시각화하여 분석할 수 있습니다.

## 기능

1. 데이터 탐색
   - 엑셀 파일 업로드
   - 검색 기능으로 데이터 필터링
   - 데이터프레임 표시

2. 분석 기능
   - 지명 빈도수 히트맵
   - 연도별 기사 수 분석
   - 키워드 워드클라우드
   - 기관 네트워크 분석

## 설치 방법

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run news_analyzer.py
```

## 의존성

- streamlit
- pandas
- plotly
- wordcloud
- networkx
- folium
- openpyxl
