import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    layout="wide"
)

st.title("서울 100년 기온 변화 분석")
st.write("1900년대 초반부터 최근까지 서울의 연평균 기온 변화 추이를 시각화합니다.")

# 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리 (UTF-8 우선 시도 후 CP949 대응)
    try:
        df = pd.read_csv(url, encoding='utf-8')
    except Exception:
        df = pd.read_csv(url, encoding='cp949')
    
    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()
    
    # 열 이름의 유연한 매핑 (괄호 유무 대응)
    date_col = [c for c in df.columns if '날짜' in c][0]
    avg_temp_col = [c for c in df.columns if '평균' in c][0]
    min_temp_col = [c for c in df.columns if '최저' in c][0]
    max_temp_col = [c for c in df.columns if '최고' in c][0]
    
    # 날짜 및 연도 데이터 변환
    df[date_col] = pd.to_datetime(df[date_col])
    df['연도'] = df[date_col].dt.year
    
    # 기온 결측치 제거
    df = df.dropna(subset=[avg_temp_col])
    
    return df, date_col, avg_temp_col, min_temp_col, max_temp_col

try:
    df, date_col, avg_temp_col, min_temp_col, max_temp_col = load_data()
    
    # 연간 관측일수가 300일 미만인 해는 데이터 불완전성으로 제외 (6.25 전쟁 기간 등)
    yearly_counts = df.groupby('연도')[avg_temp_col].count()
    valid_years = yearly_counts[yearly_counts >= 300].index
    df_valid = df[df['연도'].isin(valid_years)]
    
    # 연도별 평균 집계
    yearly_summary = df_valid.groupby('연도').agg(
        연평균기온=(avg_temp_col, 'mean'),
        연평균최저기온=(min_temp_col, 'mean'),
        연평균최고기온=(max_temp_col, 'mean')
    ).reset_index()
    
    # 사이드바 설정
    st.sidebar.header("분석 옵션")
    window_size = st.sidebar.slider("추세선 이동평균 범위(년)", min_value=1, max_value=20, value=5)
    
    # 이동평균 계산
    yearly_summary['이동평균'] = yearly_summary['연평균기온'].rolling(window=window_size, min_periods=1).mean()
    
    # 주요 요약 지표 출력
    col1, col2, col3, col4 = st.columns(4)
    min_year = int(yearly_summary['연도'].min())
    max_year = int(yearly_summary['연도'].max())
    overall_avg = yearly_summary['연평균기온'].mean()
    hottest_row = yearly_summary.loc[yearly_summary['연평균기온'].idxmax()]
    coolest_row = yearly_summary.loc[yearly_summary['연평균기온'].idxmin()]
    
    col1.metric("분석 기간", f"{min_year}년 ~ {max_year}년")
    col2.metric("전체 기간 평균기온", f"{overall_avg:.1f} ℃")
    col3.metric("최고 연평균기온", f"{hottest_row['연평균기온']:.1f} ℃ ({int(hottest_row['연도'])}년)")
    col4.metric("최저 연평균기온", f"{coolest_row['연평균기온']:.1f} ℃ ({int(coolest_row['연도'])}년)")
    
    # Plotly 시각화 (웹 폰트 사용으로 한글 깨짐 방지)
    fig = px.line(
        yearly_summary,
        x='연도',
        y=['연평균기온', '이동평균'],
        title=f"서울 연평균 기온 및 {window_size}년 이동평균 변화 추이",
        labels={'value': '기온 (℃)', 'variable': '구분', '연도': '연도'},
        markers=True
    )
    
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="연도",
        yaxis_title="기온 (℃)",
        legend_title_text="구분"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 원본 데이터 테이블 표시
    with st.expander("연도별 요약 데이터 확인"):
        st.dataframe(
            yearly_summary.style.format({
                '연평균기온': '{:.2f}',
                '연평균최저기온': '{:.2f}',
                '연평균최고기온': '{:.2f}',
                '이동평균': '{:.2f}'
            }),
            use_container_width=True
        )

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
