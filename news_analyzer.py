import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
from collections import Counter, defaultdict
import networkx as nx
import re
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
from pathlib import Path
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

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
            # 시군구 좌표 데이터 로드
            @st.cache_data
            def load_sigungu_coordinates():
                """시군구 좌표 데이터를 로드"""
                try:
                    # 현재 스크립트의 디렉토리 경로를 기준으로 파일 찾기
                    script_dir = Path(__file__).parent
                    coords_df = pd.read_csv(script_dir / 'sigungu_coordinates.csv', encoding='utf-8-sig')
                    # 좌표 사전 생성 (시군구명 -> (위도, 경도))
                    coords_dict = {}
                    for _, row in coords_df.iterrows():
                        if pd.notna(row['sigungu']):
                            coords_dict[row['sigungu']] = (row['lat'], row['lon'])
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
                    
                    for keywords in keywords_series.dropna():
                        if not isinstance(keywords, str):
                            continue
                            
                        # 한국어 키워드를 다양한 구분자로 분리
                        for kw in re.split(r'[\s,;:/()]+', keywords.strip()):
                            kw = kw.strip()
                            # 키워드가 비어있거나 너무 짧으면 건너뛰기
                            if not kw or len(kw) < 2:
                                continue
                                
                            # 시군구명과 일치하는 키워드 찾기
                            for location in coords_dict.keys():
                                if location in kw:
                                    # 정확한 단어 매칭이면 더 높은 가중치 부여
                                    if kw == location:
                                        location_counts[location] += 2  # 정확한 매칭은 2점
                                    else:
                                        location_counts[location] += 1  # 부분 매칭은 1점
                                    break
                    
                    return location_counts
                
                # 지명 빈도수 계산
                location_counts = get_location_frequency(display_df['키워드'], coords_dict)
                
                if location_counts:
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
        else:
            st.warning("업로드한 파일에 '키워드' 열이 없습니다.")
            
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
            wc = WordCloud(
                font_path="C:/Windows/Fonts/malgun.ttf",  # Windows 한글 폰트 경로
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
            
    except Exception as e:
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