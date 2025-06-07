import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
from collections import Counter
from collections import Counter, defaultdict
import networkx as nx
import re
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import os
import json
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# WordCloud에 사용할 폰트 경로 설정
import os
import platform

# Windows에서 Malgun Gothic 폰트의 경로
if platform.system() == 'Windows':
    font_path = os.path.join(os.environ['WINDIR'], 'Fonts', 'malgun.ttf')
else:
    # 다른 시스템에서는 기본 폰트 사용
    font_path = None

# 페이지 설정
st.set_page_config(
    page_title="뉴스 데이터 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("📰 뉴스 데이터 분석 대시보드")

# 파일 업로드
uploaded_file = st.file_uploader("뉴스 데이터 파일을 업로드하세요 (xlsx)", type=["xlsx"])

# 데이터 처리 함수
def process_data(uploaded_file):
    try:
        # 엑셀 파일 로드
        news_df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # 컬럼 이름 매핑
        column_mapping = {
            "일자": "작성/게시일자",
            "제목": "기사제목",
            "기관": "관련기관",
            "특성추출(가중치순 상위 50개)": "키워드",
            "URL": "기사링크"
        }
        
        # 기존 컬럼 중 매핑된 컬럼만 선택
        existing_columns = [col for col in column_mapping.keys() if col in news_df.columns]
        news_df = news_df[existing_columns]
        
        # 컬럼 이름 변경
        news_df = news_df.rename(columns=column_mapping)
        
        # 중복 컬럼 제거
        news_df = news_df.loc[:, ~news_df.columns.duplicated()]
        
        # '일자' 컬럼에서 '연도' 컬럼 생성
        if '작성/게시일자' in news_df.columns:
            try:
                # yyyymmdd 형식에서 앞의 4자리(연도) 추출
                news_df['연도'] = news_df['작성/게시일자'].astype(str).str[:4]
            except Exception as e:
                st.error(f"'일자' 컬럼에서 연도를 추출하는 중 오류가 발생했습니다: {e}")
                raise
        else:
            st.error("파일에 '일자' 컬럼이 없습니다. 분석을 종료합니다.")
            raise ValueError("일자 컬럼 없음")
            
        return news_df
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        raise

if uploaded_file is not None:
    try:
        # 데이터 처리
        news_df = process_data(uploaded_file)
        
        # 데이터 표시
        st.markdown("---")
        st.header("📊 데이터 탐색")
        
        # 검색 기능 추가
        search_text = st.text_input("검색어 입력", "")
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
        st.info("오류가 발생하여 분석을 종료합니다.")
        raise
        
    if search_text:
            # 모든 텍스트 컬럼에서 검색어가 포함된 데이터 필터링
            filtered_df = news_df[
                news_df.apply(
                    lambda row: any(search_text.lower() in str(cell).lower() 
                                   for cell in row if pd.notna(cell)),
                    axis=1
                )
            ]
            
            if len(filtered_df) == 0:
                st.warning(f"'{search_text}'에 해당하는 데이터가 없습니다.")
            else:
                st.write(f"검색 결과: {len(filtered_df)}건")
                display_df = filtered_df
    else:
        display_df = news_df
        
    # 데이터 표시 설정
    st.dataframe(
        display_df[["작성/게시일자", "기사제목", "관련기관", "키워드", "기사링크"]].head(50),
        use_container_width=True
    )
        
    # 지명 빈도수 히트맵
    st.markdown("---")
    st.header("🗺️ 분석 0: 지명 빈도수 히트맵")
    
    if '키워드' in display_df.columns:
        # 시군구 좌표 데이터를 직접 정의
        @st.cache_data
        def load_sigungu_coordinates():
            """시군구 좌표 데이터를 로드"""
            try:
                # 시군구 좌표 데이터 (직접 정의)
                coords_dict = {
  "춘천시": {
    "lat": 37.8907502944142,
    "lon": 127.73855024742944
  },
  "원주시": {
    "lat": 37.30827214389988,
    "lon": 127.93010148359669
  },
  "강릉시": {
    "lat": 37.70909757680244,
    "lon": 128.83629661662167
  },
  "동해시": {
    "lat": 37.507699146772026,
    "lon": 129.05750815396124
  },
  "태백시": {
    "lat": 37.17355382230187,
    "lon": 128.98028444413865
  },
  "속초시": {
    "lat": 38.17460699655262,
    "lon": 128.5170283057989
  },
  "삼척시": {
    "lat": 37.27940030984353,
    "lon": 129.11945855070846
  },
  "홍천군": {
    "lat": 37.745371983968425,
    "lon": 128.0718188529946
  },
  "횡성군": {
    "lat": 37.50979568781028,
    "lon": 128.07714655993058
  },
  "영월군": {
    "lat": 37.20365761082058,
    "lon": 128.5007363393495
  },
  "평창군": {
    "lat": 37.55952175453339,
    "lon": 128.4839378899835
  },
  "정선군": {
    "lat": 37.37954498871875,
    "lon": 128.736643231494
  },
  "철원군": {
    "lat": 38.23985557501652,
    "lon": 127.39553990592204
  },
  "화천군": {
    "lat": 38.13775940152845,
    "lon": 127.68466235514624
  },
  "양구군": {
    "lat": 38.17516332931209,
    "lon": 127.99809563638968
  },
  "인제군": {
    "lat": 38.065852635216366,
    "lon": 128.26556442674826
  },
  "고성군": {
    "lat": 35.016863611674,
    "lon": 128.29527118964077
  },
  "양양군": {
    "lat": 38.00454775494876,
    "lon": 128.5963809162701
  },
  "장안구": {
    "lat": 37.31396485048892,
    "lon": 127.00322224854732
  },
  "권선구": {
    "lat": 37.26162810834032,
    "lon": 126.97987706528563
  },
  "팔달구": {
    "lat": 37.27884128987851,
    "lon": 127.01638583032246
  },
  "영통구": {
    "lat": 37.27422255144783,
    "lon": 127.05332283278976
  },
  "수정구": {
    "lat": 37.434236154404296,
    "lon": 127.1034291981654
  },
  "중원구": {
    "lat": 37.43393959749726,
    "lon": 127.1630745575102
  },
  "분당구": {
    "lat": 37.37817354595352,
    "lon": 127.10522691772942
  },
  "의정부시": {
    "lat": 37.73619730554574,
    "lon": 127.0670189089998
  },
  "안양시만안구": {
    "lat": 37.403885152929206,
    "lon": 126.911729272389
  },
  "안양시동안구": {
    "lat": 37.40139490855061,
    "lon": 126.95643278057705
  },
  "부천시": {
    "lat": 37.50522462023604,
    "lon": 126.7904649625358
  },
  "광명시": {
    "lat": 37.446200498704,
    "lon": 126.8625286355182
  },
  "평택시": {
    "lat": 37.01068236511996,
    "lon": 126.98700016798088
  },
  "동두천시": {
    "lat": 37.91671220772368,
    "lon": 127.07781784130871
  },
  "안산시상록구": {
    "lat": 37.31860875318384,
    "lon": 126.87300219812454
  },
  "안산시단원구": {
    "lat": 37.52796410994512,
    "lon": 127.26693141604696
  },
  "고양시덕양구": {
    "lat": 37.65492277017285,
    "lon": 126.88019242261728
  },
  "고양시일산동구": {
    "lat": 37.67902616693949,
    "lon": 126.79746135506062
  },
  "고양시일산서구": {
    "lat": 37.68085153316388,
    "lon": 126.72620011421677
  },
  "과천시": {
    "lat": 37.43231027806656,
    "lon": 127.0064804945684
  },
  "구리시": {
    "lat": 37.59626868754476,
    "lon": 127.13173213408334
  },
  "남양주시": {
    "lat": 37.66376958720197,
    "lon": 127.24116459316475
  },
  "오산시": {
    "lat": 37.16322521948571,
    "lon": 127.05215305867264
  },
  "시흥시": {
    "lat": 37.38900482051256,
    "lon": 126.78719963286376
  },
  "군포시": {
    "lat": 37.344281230131365,
    "lon": 126.92514007145316
  },
  "의왕시": {
    "lat": 37.36203120919595,
    "lon": 126.990096388102
  },
  "하남시": {
    "lat": 37.52045955405907,
    "lon": 127.20393343514904
  },
  "용인시처인구": {
    "lat": 37.20679625043835,
    "lon": 127.24990044556256
  },
  "용인시기흥구": {
    "lat": 37.26672185641,
    "lon": 127.1195778241828
  },
  "용인시수지구": {
    "lat": 37.33281914094321,
    "lon": 127.0702202325529
  },
  "파주시": {
    "lat": 37.85600239962601,
    "lon": 126.81255683726994
  },
  "이천시": {
    "lat": 37.20706128532365,
    "lon": 127.48049856818844
  },
  "안성시": {
    "lat": 37.03389187453632,
    "lon": 127.30246925162368
  },
  "김포시": {
    "lat": 37.680627473672914,
    "lon": 126.62642298189238
  },
  "화성시": {
    "lat": 37.16482956994478,
    "lon": 126.87339687869596
  },
  "광주시": {
    "lat": 37.404450030613575,
    "lon": 127.30268236367672
  },
  "양주시": {
    "lat": 37.81000704061461,
    "lon": 127.00323756671858
  },
  "포천시": {
    "lat": 37.9736971764198,
    "lon": 127.25209888131651
  },
  "여주시": {
    "lat": 37.30404354451096,
    "lon": 127.61537735285752
  },
  "연천군": {
    "lat": 38.09161800631988,
    "lon": 127.02434936058864
  },
  "가평군": {
    "lat": 37.81788827737884,
    "lon": 127.4483909411812
  },
  "양평군": {
    "lat": 37.51843906690636,
    "lon": 127.57589149638748
  },
  "의창구": {
    "lat": 35.31232454784483,
    "lon": 128.64967174955456
  },
  "성산구": {
    "lat": 35.19871988040746,
    "lon": 128.6742461647883
  },
  "마산합포구": {
    "lat": 35.138355967347366,
    "lon": 128.48252440512871
  },
  "마산회원구": {
    "lat": 35.232852397212305,
    "lon": 128.53408754179893
  },
  "진해구": {
    "lat": 35.129877701622,
    "lon": 128.73989914938824
  },
  "진주시": {
    "lat": 35.206544753448114,
    "lon": 128.12609271157532
  },
  "통영시": {
    "lat": 34.9602477837962,
    "lon": 128.4281554826381
  },
  "사천시": {
    "lat": 35.05139368642952,
    "lon": 128.0402941918309
  },
  "김해시": {
    "lat": 35.270946015644085,
    "lon": 128.84651605170973
  },
  "밀양시": {
    "lat": 35.49826761272739,
    "lon": 128.7873196954975
  },
  "거제시": {
    "lat": 34.866266999598786,
    "lon": 128.6197335021494
  },
  "양산시": {
    "lat": 35.402140910580634,
    "lon": 129.04040629012525
  },
  "의령군": {
    "lat": 35.39231831535562,
    "lon": 128.27709824399133
  },
  "함안군": {
    "lat": 35.291331593557686,
    "lon": 128.43010811894683
  },
  "창녕군": {
    "lat": 35.50921745576266,
    "lon": 128.49292933986155
  },
  "남해군": {
    "lat": 34.796690416299455,
    "lon": 127.90734336444626
  },
  "하동군": {
    "lat": 35.13826757344309,
    "lon": 127.77760029099052
  },
  "산청군": {
    "lat": 35.36886845792488,
    "lon": 127.88557450494412
  },
  "함양군": {
    "lat": 35.55384486864036,
    "lon": 127.7226647555179
  },
  "거창군": {
    "lat": 35.73283280870575,
    "lon": 127.90449110040171
  },
  "합천군": {
    "lat": 35.57620863614838,
    "lon": 128.14220357461588
  },
  "남구": {
    "lat": 35.51703201513299,
    "lon": 129.33123504097898
  },
  "북구": {
    "lat": 35.61007506150729,
    "lon": 129.37963250576814
  },
  "경주시": {
    "lat": 35.82851022928526,
    "lon": 129.23476872051808
  },
  "김천시": {
    "lat": 36.06416818527858,
    "lon": 128.07895260021033
  },
  "안동시": {
    "lat": 36.58117835044659,
    "lon": 128.78190102442738
  },
  "구미시": {
    "lat": 36.207894175066976,
    "lon": 128.3585528280437
  },
  "영주시": {
    "lat": 36.87112334654928,
    "lon": 128.5958617527594
  },
  "영천시": {
    "lat": 36.016072766713634,
    "lon": 128.94037080539204
  },
  "상주시": {
    "lat": 36.42998993075332,
    "lon": 128.0662996426512
  },
  "문경시": {
    "lat": 36.69114841044764,
    "lon": 128.15086675306785
  },
  "경산시": {
    "lat": 35.835693488089525,
    "lon": 128.80974390764428
  },
  "군위군": {
    "lat": 36.17008046203495,
    "lon": 128.6477900492677
  },
  "의성군": {
    "lat": 36.36143281049499,
    "lon": 128.61883529114533
  },
  "청송군": {
    "lat": 36.357046010015154,
    "lon": 129.057141728659
  },
  "영양군": {
    "lat": 36.6949527205354,
    "lon": 129.1434174540719
  },
  "영덕군": {
    "lat": 36.48181335867197,
    "lon": 129.31792842448868
  },
  "청도군": {
    "lat": 35.67324707364347,
    "lon": 128.7857934852976
  },
  "고령군": {
    "lat": 35.735369942463684,
    "lon": 128.30416575625685
  },
  "성주군": {
    "lat": 35.90824796539297,
    "lon": 128.23191760753923
  },
  "칠곡군": {
    "lat": 36.015681391514185,
    "lon": 128.4613013104463
  },
  "예천군": {
    "lat": 36.6510755762577,
    "lon": 128.42254745389164
  },
  "봉화군": {
    "lat": 36.93369419408296,
    "lon": 128.91277878909182
  },
  "울진군": {
    "lat": 36.90459921719136,
    "lon": 129.3111737614945
  },
  "울릉군": {
    "lat": 37.50231064973898,
    "lon": 130.86050905549277
  },
  "동구": {
    "lat": 37.48170978664167,
    "lon": 126.64377577568258
  },
  "서구": {
    "lat": 37.55760545100642,
    "lon": 126.65875260943754
  },
  "광산구": {
    "lat": 35.16467726243392,
    "lon": 126.7501967453198
  },
  "중구": {
    "lat": 37.479388756128536,
    "lon": 126.44538433256218
  },
  "수성구": {
    "lat": 35.833450308581206,
    "lon": 128.65949008781337
  },
  "달서구": {
    "lat": 35.82716724401521,
    "lon": 128.52891150529214
  },
  "달성군": {
    "lat": 35.689667397774954,
    "lon": 128.5255499483045
  },
  "유성구": {
    "lat": 36.37968678653291,
    "lon": 127.33622288367712
  },
  "대덕구": {
    "lat": 36.41663639588057,
    "lon": 127.4420928164686
  },
  "부산진구": {
    "lat": 35.16372190233443,
    "lon": 129.04252470861604
  },
  "동래구": {
    "lat": 35.20326022722132,
    "lon": 129.0808539747662
  },
  "해운대구": {
    "lat": 35.196195892954336,
    "lon": 129.1549174682266
  },
  "사하구": {
    "lat": 35.09385812595978,
    "lon": 128.97195189058598
  },
  "금정구": {
    "lat": 35.2595241937298,
    "lon": 129.09325162920206
  },
  "강서구": {
    "lat": 37.56186978699498,
    "lon": 126.82566770777774
  },
  "연제구": {
    "lat": 35.17787570663703,
    "lon": 129.08362449375278
  },
  "수영구": {
    "lat": 35.16127645824772,
    "lon": 129.11182719765745
  },
  "사상구": {
    "lat": 35.16277459525929,
    "lon": 128.98969511568666
  },
  "기장군": {
    "lat": 35.30166448647811,
    "lon": 129.201986214536
  },
  "종로구": {
    "lat": 37.59446375034286,
    "lon": 126.97844273422751
  },
  "용산구": {
    "lat": 37.53058863020561,
    "lon": 126.9784805209122
  },
  "성동구": {
    "lat": 37.54920970923639,
    "lon": 127.04056253356858
  },
  "광진구": {
    "lat": 37.54831760030002,
    "lon": 127.08664293895676
  },
  "동대문구": {
    "lat": 37.581378576424775,
    "lon": 127.05422835430224
  },
  "중랑구": {
    "lat": 37.59712357387402,
    "lon": 127.09146588655774
  },
  "성북구": {
    "lat": 37.60571665591892,
    "lon": 127.01755738229808
  },
  "강북구": {
    "lat": 37.64226476054209,
    "lon": 127.01118085815442
  },
  "도봉구": {
    "lat": 37.66808245399668,
    "lon": 127.03233526682952
  },
  "노원구": {
    "lat": 37.650025755961295,
    "lon": 127.07541964378458
  },
  "은평구": {
    "lat": 37.619224355567255,
    "lon": 126.92587753102518
  },
  "서대문구": {
    "lat": 37.57845051844033,
    "lon": 126.93915290118034
  },
  "마포구": {
    "lat": 37.560386497598365,
    "lon": 126.90636517167935
  },
  "양천구": {
    "lat": 37.52604459229557,
    "lon": 126.85359499921948
  },
  "구로구": {
    "lat": 37.49671695797304,
    "lon": 126.85866623045672
  },
  "금천구": {
    "lat": 37.45987210562151,
    "lon": 126.90135000345822
  },
  "영등포구": {
    "lat": 37.52226409863389,
    "lon": 126.90990611335108
  },
  "동작구": {
    "lat": 37.49926262560018,
    "lon": 126.95114855188169
  },
  "관악구": {
    "lat": 37.467572112554784,
    "lon": 126.94648519450028
  },
  "서초구": {
    "lat": 37.47375670670706,
    "lon": 127.02824862352315
  },
  "강남구": {
    "lat": 37.49500863430103,
    "lon": 127.06447729739476
  },
  "송파구": {
    "lat": 37.505585493847576,
    "lon": 127.11562474009423
  },
  "강동구": {
    "lat": 37.5503441892287,
    "lon": 127.14725283554372
  },
  "세종특별자치시": {
    "lat": 36.55956618377621,
    "lon": 127.26028592082076
  },
  "울주군": {
    "lat": 35.548739418527184,
    "lon": 129.18298519280313
  },
  "미추홀구": {
    "lat": 37.45254978134102,
    "lon": 126.66399631524844
  },
  "연수구": {
    "lat": 37.4009921896573,
    "lon": 126.64993493605672
  },
  "남동구": {
    "lat": 37.43143986534312,
    "lon": 126.72611321843482
  },
  "부평구": {
    "lat": 37.49763356643621,
    "lon": 126.7208188462943
  },
  "계양구": {
    "lat": 37.5572442708194,
    "lon": 126.73811099103708
  },
  "강화군": {
    "lat": 37.71767824101647,
    "lon": 126.43997890004856
  },
  "옹진군": {
    "lat": 38.41688828537046,
    "lon": 123.72871393725173
  },
  "목포시": {
    "lat": 34.812716944614664,
    "lon": 126.40455215832884
  },
  "여수시": {
    "lat": 34.77180839117281,
    "lon": 127.65528521137462
  },
  "순천시": {
    "lat": 34.99447630457818,
    "lon": 127.38999557134534
  },
  "나주시": {
    "lat": 34.987417843227256,
    "lon": 126.7213048158046
  },
  "광양시": {
    "lat": 35.02802399419046,
    "lon": 127.65161482183989
  },
  "담양군": {
    "lat": 35.29050729318408,
    "lon": 126.99872419628464
  },
  "곡성군": {
    "lat": 35.21683673776393,
    "lon": 127.264548917215
  },
  "구례군": {
    "lat": 35.23796069077802,
    "lon": 127.50451008267986
  },
  "고흥군": {
    "lat": 34.61162681819536,
    "lon": 127.30806274268446
  },
  "보성군": {
    "lat": 34.8136505937168,
    "lon": 127.16020783679414
  },
  "화순군": {
    "lat": 35.00691278818029,
    "lon": 127.03337673544772
  },
  "장흥군": {
    "lat": 34.67712003090553,
    "lon": 126.92281874858804
  },
  "강진군": {
    "lat": 34.62316246691055,
    "lon": 126.77113878908828
  },
  "해남군": {
    "lat": 34.54318580117218,
    "lon": 126.52484023612097
  },
  "영암군": {
    "lat": 34.79892908395468,
    "lon": 126.6282033706885
  },
  "무안군": {
    "lat": 34.95657948704523,
    "lon": 126.42294509641756
  },
  "함평군": {
    "lat": 35.11174623509192,
    "lon": 126.53407194047718
  },
  "영광군": {
    "lat": 35.28018512305113,
    "lon": 126.46237168483232
  },
  "장성군": {
    "lat": 35.329754239139994,
    "lon": 126.76932549930804
  },
  "완도군": {
    "lat": 34.35395816317371,
    "lon": 126.8067569307662
  },
  "진도군": {
    "lat": 34.45903834913944,
    "lon": 126.24161362945188
  },
  "신안군": {
    "lat": 34.766287625210715,
    "lon": 126.01661363536137
  },
  "전주시완산구": {
    "lat": 35.79125243910566,
    "lon": 127.12032639331838
  },
  "전주시덕진구": {
    "lat": 35.85836611128281,
    "lon": 127.11295996539803
  },
  "군산시": {
    "lat": 35.95362670889988,
    "lon": 126.7443737203119
  },
  "익산시": {
    "lat": 36.02213912940299,
    "lon": 126.98932369227764
  },
  "정읍시": {
    "lat": 35.60140092021863,
    "lon": 126.9063570780874
  },
  "남원시": {
    "lat": 35.4227422389565,
    "lon": 127.44519131270307
  },
  "김제시": {
    "lat": 35.806631311753456,
    "lon": 126.89956022387092
  },
  "완주군": {
    "lat": 35.92733544437608,
    "lon": 127.23172502709389
  },
  "진안군": {
    "lat": 35.82837665077507,
    "lon": 127.43038917104975
  },
  "무주군": {
    "lat": 35.93985637256399,
    "lon": 127.71292479404538
  },
  "장수군": {
    "lat": 35.65758995372194,
    "lon": 127.54422713953508
  },
  "임실군": {
    "lat": 35.595851307940784,
    "lon": 127.23548510615304
  },
  "순창군": {
    "lat": 35.43318214668328,
    "lon": 127.09225142521862
  },
  "고창군": {
    "lat": 35.45016976388217,
    "lon": 126.617665990879
  },
  "부안군": {
    "lat": 35.67904577575091,
    "lon": 126.65393168215302
  },
  "제주시": {
    "lat": 33.43690726655745,
    "lon": 126.5275428536248
  },
  "서귀포시": {
    "lat": 33.3247589974335,
    "lon": 126.5814193223849
  },
  "천안시동남구": {
    "lat": 36.76285671728634,
    "lon": 127.22106349717696
  },
  "천안시서북구": {
    "lat": 36.89133588039875,
    "lon": 127.15991121313095
  },
  "공주시": {
    "lat": 36.48013100340541,
    "lon": 127.07526448032309
  },
  "보령시": {
    "lat": 36.34376024925245,
    "lon": 126.60358066470836
  },
  "아산시": {
    "lat": 36.807980591986826,
    "lon": 126.9780781633212
  },
  "서산시": {
    "lat": 36.78101306907095,
    "lon": 126.4653509723483
  },
  "논산시": {
    "lat": 36.19161507021065,
    "lon": 127.15959200382568
  },
  "계룡시": {
    "lat": 36.29639733338959,
    "lon": 127.23409744669732
  },
  "당진시": {
    "lat": 36.903428540137526,
    "lon": 126.65288268363548
  },
  "금산군": {
    "lat": 36.11949795650293,
    "lon": 127.4774275852492
  },
  "부여군": {
    "lat": 36.24485988467384,
    "lon": 126.85872075276473
  },
  "서천군": {
    "lat": 36.1086701278833,
    "lon": 126.70587754361448
  },
  "청양군": {
    "lat": 36.429944989673146,
    "lon": 126.85043582291672
  },
  "홍성군": {
    "lat": 36.56977359648989,
    "lon": 126.62416591391433
  },
  "예산군": {
    "lat": 36.67121358707068,
    "lon": 126.78316762079383
  },
  "태안군": {
    "lat": 36.876597834635625,
    "lon": 126.21257450315706
  },
  "상당구": {
    "lat": 36.59457486050864,
    "lon": 127.5866844432612
  },
  "서원구": {
    "lat": 36.54712693515592,
    "lon": 127.4398223100628
  },
  "흥덕구": {
    "lat": 36.64728717277419,
    "lon": 127.36945304046684
  },
  "청원구": {
    "lat": 36.72106598414242,
    "lon": 127.4915211803271
  },
  "충주시": {
    "lat": 37.01297816188485,
    "lon": 127.89434787829916
  },
  "제천시": {
    "lat": 37.05934659325082,
    "lon": 128.1413213779792
  },
  "보은군": {
    "lat": 36.48943538388814,
    "lon": 127.72625168222108
  },
  "옥천군": {
    "lat": 36.32018550243811,
    "lon": 127.65751363249878
  },
  "영동군": {
    "lat": 36.15921351501756,
    "lon": 127.81014273456776
  },
  "증평군": {
    "lat": 36.78559015021481,
    "lon": 127.60564013659555
  },
  "진천군": {
    "lat": 36.86943906186885,
    "lon": 127.44356748731671
  },
  "괴산군": {
    "lat": 36.76657974619426,
    "lon": 127.8275782644069
  },
  "음성군": {
    "lat": 36.97438578796661,
    "lon": 127.61566647572856
  },
  "단양군": {
    "lat": 36.99500218415685,
    "lon": 128.38871042193472
  }                        
                }
                return coords_dict
            except Exception as e:
                st.error(f"시군구 좌표 로드 중 오류: {e}")
                return {}
            
        coords_dict = load_sigungu_coordinates()
            
        if coords_dict:
            # 키워드에서 지명 추출 및 빈도수 계산
            def get_location_frequency(keywords_series, coords_dict):
                """키워드 시리즈에서 지명 빈도수를 계산"""
                location_counts = defaultdict(int)

                # 모든 시군구명에서 접미사를 제거한 기본 이름만 저장
                base_names = {loc: loc.replace('시', '').replace('군', '').replace('구', '') 
                  for loc in coords_dict.keys()}
    
                for keywords in keywords_series.dropna():
                    if not isinstance(keywords, str):
                        continue
            
                # 한국어 키워드를 다양한 구분자로 분리
                for kw in re.split(r'[\s,;:/()]+', keywords.strip()):
                    kw = kw.strip()
                    if not kw or len(kw) < 2:
                        continue
                
                # 접미사 제거한 키워드로 비교
                kw_base = kw.replace('시', '').replace('군', '').replace('구', '')
            
                # 모든 시군구명과 비교
                for location, base_name in base_names.items():
                    if base_name in kw_base:
                        # 정확한 매치는 더 높은 가중치 부여
                        if kw_base == base_name:
                            location_counts[location] += 3
                        else:
                            location_counts[location] += 1
                        break

                return location_counts
                
            # 지명 빈도수 계산
            location_counts = get_location_frequency(display_df['키워드'], coords_dict)
    
            if location_counts and sum(location_counts.values()) > 0:
                # 히트맵 생성
                def create_heatmap(location_counts, coords_dict):
                    """지명 빈도수를 기반으로 히트맵 생성"""
                    # 데이터프레임 생성
                    df_locations = pd.DataFrame({
                        'location': list(location_counts.keys()),
                        'count': list(location_counts.values())
                        })
                        
                    # 좌표 추가
                    df_locations['lat'] = df_locations['location'].apply(
                        lambda x: coords_dict.get(x, (None, None))[0] if x in coords_dict else None
                    )
                    df_locations['lon'] = df_locations['location'].apply(
                        lambda x: coords_dict.get(x, (None, None))[1] if x in coords_dict else None
                        )
                        
                    # 좌표가 없는 행 제거
                    df_locations = df_locations.dropna(subset=['lat', 'lon'])
                        
                    if df_locations.empty:
                        st.warning("유효한 좌표 데이터가 없습니다.")
                        return None
                        
                    # 지도 생성 (한국 중심)
                    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles='cartodbpositron')
                        
                    # 히트맵 데이터 준비
                    heat_data = [[row['lat'], row['lon'], row['count']] for _, row in df_locations.iterrows()]
                        
                    # 히트맵 추가
                    HeatMap(heat_data, radius=15, blur=10).add_to(m)
                        
                    # 상위 10개 지명에 마커 추가
                    top_locations = df_locations.nlargest(10, 'count')
                    for _, row in top_locations.iterrows():
                        folium.CircleMarker(
                            location=[row['lat'], row['lon']],
                            radius=row['count']/max(df_locations['count'])*10 + 5,
                            popup=f"{row['location']}: {row['count']}건",
                            color='blue',
                            fill=True,
                            fill_opacity=0.4
                            ).add_to(m)
                        
                    return m
                    
                # 히트맵 생성 및 표시
                st.markdown("### 🗺️ 지명 빈도수 히트맵")
                heatmap = create_heatmap(location_counts, coords_dict)
                if heatmap:
                    folium_static(heatmap, width=800, height=600)
                    
                # 상위 20개 지명 표시
                st.markdown("### 📊 지명 빈도수 Top 20")
                df_top = pd.DataFrame({
                    '지명': list(location_counts.keys()),
                    '빈도수': list(location_counts.values())
                    }).sort_values('빈도수', ascending=False).head(20)
                    
                # 빈도수에 따른 색상 그라데이션 적용
                st.dataframe(
                    df_top.style.background_gradient(cmap='YlOrRd', subset=['빈도수']),
                    use_container_width=True
                    )
            else:
                st.warning("키워드에서 인식된 지명이 없습니다.")
            
        # 연도별 기사 수 분석
        st.markdown("---")
        st.header("🗺️ 분석 1: 연도별 기사 수 분석")
        
        if '연도' in display_df.columns:
            year_counts = display_df["연도"].value_counts().sort_index()
            
            fig1 = px.bar(
                x=year_counts.index,
                y=year_counts.values,
                labels={"x": "연도", "y": "기사 수"},
                title="연도별 기사 수 분석"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.error("'연도' 컬럼이 생성되지 않았습니다. 데이터를 다시 확인해주세요.")
            st.stop()
        
        # 키워드 워드클라우드 분석
        st.markdown("---")
        st.header("☁️ 분석 2: 키워드 워드클라우드")
        
        if '키워드' in display_df.columns:
            # 키워드 처리
            all_keywords = ",".join(display_df["키워드"].dropna().astype(str)).split(",")
            filtered_keywords = [kw.strip() for kw in all_keywords if len(kw.strip()) > 1]
            keyword_freq = Counter(filtered_keywords)
            
            # 워드클라우드에 표시할 상위 키워드 수 조정
            st.subheader("워드클라우드 설정")
            top_n = st.slider("표시할 상위 키워드 수", 10, 100, 20, 10)
            top_keywords = dict(keyword_freq.most_common(top_n))
            
            # 워드클라우드 생성
            try:
                # Try to use a system font for Korean text
                wc = WordCloud(
                    font_path="NanumGothic",  # Try to use system font
                    background_color="white",
                    width=800,
                    height=400
                ).generate_from_frequencies(top_keywords)
            except:
                # Fallback to default font if system font is not available
                wc = WordCloud(
                    background_color="white",
                    width=800,
                    height=400
                ).generate_from_frequencies(top_keywords)
            
            # 워드클라우드 표시
            st.set_option('deprecation.showPyplotGlobalUse', False)
            plt.figure(figsize=(12, 6))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            st.pyplot()
        else:
            st.warning("업로드한 파일에 '키워드' 열이 없습니다.")
            
        # 기관 네트워크 분석
        st.markdown("---")
        st.header("🕸️ 분석 3: 기관 네트워크 분석")
        
        if '관련기관' in display_df.columns:
            # 기관 네트워크 분석
            co_occurrence = Counter()
            for row in display_df["관련기관"].dropna():
                orgs = list(set([o.strip() for o in str(row).split(",") if len(o.strip()) > 1]))
                for i in range(len(orgs)):
                    for j in range(i+1, len(orgs)):
                        edge = tuple(sorted([orgs[i], orgs[j]]))
                        co_occurrence[edge] += 1
            
            # 동시출현 2회 이상만 필터링
            filtered_edges = {pair: w for pair, w in co_occurrence.items() if w >= 2}
            
            G = nx.Graph()
            for (a, b), weight in filtered_edges.items():
                G.add_edge(a, b, weight=weight)
            
            if len(G.nodes()) > 0:
                # 상위 노드 수 조절 슬라이더
                max_nodes = min(30, len(G.nodes()))  # 최대 50개 노드로 제한
                node_count = st.slider("분석할 상위 기관 수", 5, max_nodes, min(20, max_nodes), 1)
                
                # 선택한 노드 수만큼 상위 노드 필터링
                top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:node_count]
                G_filtered = G.subgraph([n for n, _ in top_nodes])
                
                st.write(f"선택된 기관 수: {len(G_filtered.nodes())}")
                st.write(f"연결 수: {len(G_filtered.edges())}")
                
                # 노드 위치 계산
                pos = nx.spring_layout(G_filtered, seed=42)
                
                # 엣지 좌표 추출
                edge_x, edge_y = [], []
                for edge in G_filtered.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x += [x0, x1, None]
                    edge_y += [y0, y1, None]
                
                # 엣지 트레이스
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.5, color="#888"),
                    hoverinfo='none',
                    mode='lines'
                )
                
                # 노드 트레이스
                node_x, node_y, node_text = [], [], []
                for node in G_filtered.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(f"{node}<br>연결 수: {G_filtered.degree[node]}")
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=[node[:10] + '...' if len(node) > 10 else node for node in G_filtered.nodes()],
                    textposition="bottom center",
                    hovertext=node_text,
                    hoverinfo='text',
                    marker=dict(
                        showscale=True,
                        colorscale='YlGnBu',
                        size=10,
                        color=[G_filtered.degree[node] for node in G_filtered.nodes()],
                        colorbar=dict(
                            thickness=15,
                            title='연결 수',
                            xanchor='left',
                            titleside='right'
                        ),
                        line_width=2
                    )
                )
                
                # 네트워크 그래프 생성
                fig = go.Figure(
                    data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("네트워크를 생성할 충분한 데이터가 없습니다.")
        else:
            st.warning("업로드한 파일에 '관련기관' 열이 없습니다.")
            
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
        st.stop()

# 스타일 설정
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stDataFrame {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)