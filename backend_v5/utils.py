# backend_v5/utils.py
import pandas as pd

def auto_filter_noise(df, keyword):
    """
    수집된 데이터 프레임에서 검색어와 관련 없는 노이즈를 자동으로 제거합니다.
    """
    if df is None or df.empty:
        return df
        
    # 1. 키워드가 본문에 포함되어 있는지 확인 (가장 확실한 순도 확보)
    df = df[df['content'].str.contains(keyword, na=False)]
    
    # 2. 너무 짧은 글(스팸/의미없음) 제거
    df = df[df['content'].str.len() > 20]
    
    return df