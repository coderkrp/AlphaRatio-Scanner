import pandas as pd
import numpy as np
from src.ratio_engine import compute_ratios_for_pair

def test_compute_ratios_for_pair_basic():
    """
    Test that the ratio is calculated correctly using simple dummy data.
    """
    # Create simple dummy data
    dates = pd.date_range('2023-01-01', periods=3, freq='D')
    
    asset_df = pd.DataFrame({
        'Close': [100.0, 110.0, 120.0],
        'Open': [90.0, 100.0, 110.0],
        'High': [105.0, 115.0, 125.0],
        'Low': [85.0, 95.0, 105.0],
        'Volume': [1000, 1100, 1200]
    }, index=dates)
    
    bench_df = pd.DataFrame({
        'Close': [10.0, 10.0, 10.0],  # Static benchmark to make math easy
        'Open': [10.0, 10.0, 10.0],
        'High': [10.0, 10.0, 10.0],
        'Low': [10.0, 10.0, 10.0],
        'Volume': [5000, 5000, 5000]
    }, index=dates)

    # Compute ratio
    ratio_df = compute_ratios_for_pair(asset_df, bench_df)

    # Verify length and indices
    assert len(ratio_df) == 3
    assert (ratio_df.index == dates).all()

    # Verify math (Asset Close / Bench Close)
    # 100/10 = 10, 110/10 = 11, 120/10 = 12
    assert np.isclose(ratio_df.iloc[0]['ratio_close'], 10.0)
    assert np.isclose(ratio_df.iloc[1]['ratio_close'], 11.0)
    assert np.isclose(ratio_df.iloc[2]['ratio_close'], 12.0)
