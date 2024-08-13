import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import plotly.express as px
# !pip install --force-reinstall --no-deps bokeh==2.4.3
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category20
from bokeh.models import HoverTool

# 데이터베이스 연결 정보
host = '121.78.124.75'
user = 'dmcmedia'
password = 'DuFaj3fa#G4q'
database = 'dmc_ad_data'
port = 3308

st.set_page_config(layout="wide")


# CSS 스타일을 사용하여 전체 폰트 패밀리 변경 및 메트릭 카드 스타일 변경
st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100..900&display=swap');

            /* 모든 텍스트 요소에 폰트 적용 */
            html, body, div, span, root, data-testid, app-view-root, [class*="css"], h1, h2, h3, h4, h5, h6 {
                font-family: 'Noto Sans KR', sans-serif !important;
            }

            /* 더 구체적인 선택자를 사용하여 스타일 적용 */    
            div[data-testid="stMetric"], div[data-testid="metric-container"] {
                background-color: #f9f9f9 !important;  /* 배경색 변경 */
                border: 1px solid #ccc !important;  /* 테두리 색상 변경 */
                padding: 5% 5% 5% 10%;
                border-radius: 5px;
                border-left: 0.5rem solid #ffa25d !important;  /* 좌측 바 색상 */
                /* box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important; */
            }
            
            /* 메트릭 카드 내부의 글씨 크기 조절 */
            div[data-testid="stMetric"] > div label {
                font-size: 0.5em;
            }
            div[data-testid="stMetric"] > div div {
                font-size: 0.5em;
            }
            div[data-testid="stMetric"] > div div[data-testid="stMetricDelta"] {
                font-size: 0.5em;
            }
            </style>
            """, unsafe_allow_html=True
            )

# 데이터베이스 호출 함수
def call_database(media_nm):
    conn = pymysql.connect(host=host, user=user, password=password, database=database, port=port, charset='utf8')
    query = f"SELECT * FROM {media_nm}"
    rawdata = pd.read_sql(query, con=conn)
    conn.close()
    
    # 전처리
    rawdata['CPM'] = rawdata['spend']/rawdata['impressions']*1000
    rawdata['CPC'] = rawdata['spend']/rawdata['clicks']
    rawdata['CPV'] = rawdata['spend']/rawdata['view_p25']
    rawdata['CTR'] = rawdata['clicks']/rawdata['impressions']*100
    rawdata['VTR'] = rawdata['view_p25']/rawdata['impressions']*100
    
    rawdata['year'] = rawdata['index'].str.split('_').str[0]
    rawdata['month'] = rawdata['index'].str.split('_').str[1]
    rawdata['year_month'] = rawdata['index'].str.split('_').str[0] + '/' + rawdata['index'].str.split('_').str[1]
    
    return rawdata

# 공통 함수: 데이터 기반 메트릭 카드 표시
def example(data, col1_name, col2_name, col3_name, col4_name, col5_name):
    col1, col2, col3, col4, col5 = st.columns(5)
    col1_avg = data[col1_name].median()
    col2_avg = data[col2_name].median()
    col3_avg = data[col3_name].median()
    col4_avg = data[col4_name].median()
    col5_avg = data[col5_name].median()
    col1.metric(label="CPM", value=round(col1_avg, 1), delta=0)
    col2.metric(label="CPC", value=round(col2_avg, 1), delta=0)
    col3.metric(label="CPV", value=round(col3_avg, 1), delta=0)
    col4.metric(label="CTR", value=round(col4_avg, 2), delta=0)
    col5.metric(label="VTR", value=round(col5_avg, 2), delta=0)
    style_metric_cards()

# 특정 데이터 컬럼에 대한 파이 차트를 생성하는 함수
def plot_pie_chart(data, column_name, color_theme='Plotly'):
    if not pd.api.types.is_numeric_dtype(data[column_name]):
        data_to_plot = data[column_name].value_counts().reset_index()
        data_to_plot.columns = [column_name, 'count']
        value_column = 'count'
    else:
        data_to_plot = data
        value_column = column_name
    top_5 = data_to_plot.nlargest(5, value_column)
    others = data_to_plot.iloc[5:].sum(numeric_only=True)[value_column]
    if others > 0:
        top_5 = top_5.append(pd.DataFrame({column_name: ['etc'], value_column: [others]}), ignore_index=True)
    color_palettes = {
        'Plotly': px.colors.qualitative.Plotly,
        'Viridis': px.colors.sequential.Viridis,
        'Cividis': px.colors.sequential.Cividis,
        'Plasma': px.colors.sequential.Plasma,
        'Custom': ['#8075ff', '#24cbde', '#ff6dab', '#ffb700', '#45b7fd']
    }
    colors = color_palettes.get(color_theme, px.colors.qualitative.Plotly)
    fig = px.pie(top_5, values=value_column, names=column_name, title=f'{column_name} 비중',
                 height=250, width=200, color_discrete_sequence=colors)
    fig.update_traces(textinfo='percent+label', textposition='inside', hoverinfo='label+percent',
                      texttemplate='%{percent:.1%}', textfont_size=13, textfont_color='white')
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=0), showlegend=True,
                      legend=dict(y=0.5, yanchor='middle', x=1.2, xanchor='left', orientation="v"),
                      uniformtext_minsize=12, uniformtext_mode='hide',
                      annotations=[dict(text='', x=0.5, y=0.5, font_size=20, showarrow=False)])
    fig.update_traces(hole=0.4, domain={'x': [0, 1], 'y': [0, 1]})
    st.plotly_chart(fig, use_container_width=True)

# 메뉴에 따른 사이드바 필터링 옵션 함수
def sidebar_filters(unique_media_names, unique_platform_position, unique_devices):
    sub_option_media = st.sidebar.selectbox("미디어 선택", unique_media_names, index=0)
    sub_option_platform_position = st.sidebar.selectbox("게재위치 선택", unique_platform_position, index=0)
    sub_option_device = st.sidebar.selectbox("Device", unique_devices, index=0)
    return sub_option_media, sub_option_platform_position, sub_option_device

# 메인 함수
def main():
    st.markdown("""
        <style>
        .css-1d391kg { padding: 1rem 1rem 1rem 1rem; }
        .css-18e3th9 { display: none; }
        .css-1v0mbdj a { font-size: 14px !important; padding: 5px 10px; }
        </style>
        """, unsafe_allow_html=True)
    

    with st.sidebar:
        menu = option_menu(None, ['메뉴1', '메뉴2', '메뉴3', '메뉴4'],
                           icons=['house', 'gear', 'envelope', 'info'],
                           menu_icon="cast", default_index=0)

    if menu == '메뉴1':
        tb_meta = call_database('tb_meta')
                
        # 사이드바 필터링 옵션
        unique_media_names = ['전체'] + tb_meta['media_name'].unique().tolist()
        unique_platform_position = ['전체'] + tb_meta['platform_position'].unique().tolist()
        unique_devices = ['전체'] + tb_meta['device'].unique().tolist()

        sub_option_media, sub_option_platform_position, sub_option_device = sidebar_filters(
            unique_media_names, unique_platform_position, unique_devices)

        temp_tb_meta = tb_meta.copy()
        
        # 메트릭 카드
        st.subheader("효율 요약")
        st.text('요약')
        example(temp_tb_meta, 'CPM', 'CPC', 'CPV', 'CTR', 'VTR')
        
        # 표 영역
        st.subheader(" ")
        st.subheader("효율 찾기")
        st.info('선택하는 컬럼에 대한 효율 및 수치를 확인할 수 있습니다. (pivot)')
        # 데이터 필터링
        if sub_option_media != '전체':
            temp_tb_meta = temp_tb_meta[temp_tb_meta['media_name'] == sub_option_media]
        if sub_option_device != '전체':
            temp_tb_meta = temp_tb_meta[temp_tb_meta['device'] == sub_option_device]

        # ***명사 컬럼과 수치 컬럼 선택 부분을 나란히 표시***
        col1, col2 = st.columns(2)
        
        with col1:
            grouping_columns = st.multiselect("기준 컬럼을 선택하세요.",
                                              options=['account_name', 'campaign_name', 'adgroup_name',
                                                       'media_name', 'platform_position', 'device'],
                                              default=['media_name', 'platform_position'])
        
        with col2:
            metric_columns = st.multiselect("수치 컬럼을 선택하세요.",
                                            options=['CPM', 'CPC', 'CPV', 'CTR', 'VTR',
                                                     'clicks', 'impressions', 'reach', 'frequency',
                                                     'view_p25', 'view_p50', 'view_p75', 'view_p100',
                                                     'spend'],
                                            default=['CPM', 'CTR', 'impressions', 'clicks', 'spend'])

        # 선택된 명사 컬럼에 따라 데이터 그룹핑 및 수치 컬럼을 집계
        if grouping_columns:
            grouped_df = temp_tb_meta.groupby(grouping_columns)[metric_columns].mean().reset_index()

            # 데이터프레임을 표시하되, 인덱스를 숨기고 최대 100개 행만 표시
            st.dataframe(grouped_df.head(100).style.hide(axis='index'), use_container_width=True)  # 인덱스 숨김, 최대 100행 표시, 전체 가로폭 사용
        else:
            st.write(" ")

        st.subheader(" ")
        st.subheader("영역입니당")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.text("첫 번째 영역")
            plot_pie_chart(temp_tb_meta, 'media_name', color_theme='Custom')
        with col2:
            st.write("두 번째 영역")
        with col3:
            st.write("세 번째 영역")
        with col4:
            st.write("네 번째 영역")

        # # *** st.bokeh_chart를 사용하여 year_month와 수치 데이터를 시각화 ***
        # # year_month 기준으로 수치 데이터 시각화
        # st.subheader("수치 데이터를 시각화")
        # selected_metrics = st.multiselect(
        #     "수치 컬럼을 선택하세요 (year_month 기준으로 시각화)",
        #     options=['CPM', 'CPC', 'CPV', 'CTR', 'VTR'],
        #     default=['CPM']
        # )

        # if selected_metrics:
        #     # year_month를 x축으로 설정하고 그룹화하여 평균 계산
        #     temp_tb_meta['year_month'] = pd.to_datetime(temp_tb_meta['year_month'])
        #     grouped_data = temp_tb_meta.groupby('year_month')[selected_metrics].mean().reset_index()
        #     grouped_data = grouped_data.sort_values('year_month')

        #     # Bokeh 시각화 준비
        #     p = figure(x_axis_type="datetime", title="수치 데이터 시각화 (year_month 기준)", height=400, width=900)
        #     p.xaxis.axis_label = 'Year/Month'
        #     p.yaxis.axis_label = 'Value'
            
        #     colors = Category20[20]  # 최대 20개 색상 제공
        #     for i, metric in enumerate(selected_metrics):
        #         p.line(grouped_data['year_month'], grouped_data[metric], legend_label=metric, line_width=2, color=colors[i % 20])
        #         p.circle(grouped_data['year_month'], grouped_data[metric], color=colors[i % 20], size=5)

        #     # HoverTool 추가
        #     hover = HoverTool()
        #     hover.tooltips = [("Year/Month", "@x{%F}"), ("Value", "@y")]
        #     hover.formatters = {'@x': 'datetime'}
        #     p.add_tools(hover)

        #     p.legend.location = "top_left"
        #     p.legend.click_policy = "hide"  # 클릭으로 선 숨기기

        #     # Bokeh 차트 출력
        #     st.bokeh_chart(p, use_container_width=True)
        
        # Bokeh 시각화 준비 대신 Plotly를 사용하여 year_month와 수치 데이터를 시각화
        st.subheader("수치 데이터를 시각화")
        selected_metrics = st.multiselect(
            "수치 컬럼을 선택하세요 (year_month 기준으로 시각화)",
            options=['CPM', 'CPC', 'CPV', 'CTR', 'VTR'],
            default=['CPM']
        )

        if selected_metrics:
            # year_month를 x축으로 설정하고 그룹화하여 평균 계산
            temp_tb_meta['year_month'] = pd.to_datetime(temp_tb_meta['year_month'])
            grouped_data = temp_tb_meta.groupby('year_month')[selected_metrics].mean().reset_index()
            grouped_data = grouped_data.sort_values('year_month')

            # Plotly 시각화 준비
            fig = px.line(grouped_data, x='year_month', y=selected_metrics,
                        title="수치 데이터 시각화 (year_month 기준)",
                        labels={'year_month': 'Year/Month', 'value': 'Value'})

            # 스타일링 추가
            fig.update_layout(
                xaxis_title="Year/Month",
                yaxis_title="Value",
                legend_title="Metrics",
                height=400,
                width=900,
                margin=dict(l=20, r=20, t=50, b=20)
            )

            # Plotly 차트 출력
            st.plotly_chart(fig, use_container_width=True)


    elif menu == '메뉴2':
        st.title("메뉴2 페이지")
        st.write("여기는 메뉴2 페이지입니다.")

    elif menu == '메뉴3':
        st.title("메뉴3 페이지")
        st.write("여기는 메뉴3 페이지입니다.")

    elif menu == '메뉴4':
        st.title("메뉴4 페이지")
        st.write("여기는 메뉴4 페이지입니다.")

if __name__ == '__main__':
    main()

