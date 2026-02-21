#!/usr/bin/env python3
"""
Validate that seasonal precipitation equals the sum of monthly precipitation.

This script checks that:
- DJF (Dec+Jan+Feb) = monthly 12 + 1 + 2
- MAM (Mar+Apr+May) = monthly 3 + 4 + 5
- JJA (Jun+Jul+Aug) = monthly 6 + 7 + 8
- SON (Sep+Oct+Nov) = monthly 9 + 10 + 11
"""

import rasterio
import numpy as np
from pathlib import Path

# Season to month mapping
SEASONS = {
    'djf': [12, 1, 2],   # December, January, February
    'mam': [3, 4, 5],    # March, April, May
    'jja': [6, 7, 8],    # June, July, August
    'son': [9, 10, 11]   # September, October, November
}

def load_raster(path):
    """Load raster data."""
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        return data

def validate_seasonal_monthly(year_range='2015-2025', tolerance=0.1):
    """
    Validate that seasonal totals equal sum of monthly totals.
    
    Args:
        year_range: Year range string (e.g., '2015-2025')
        tolerance: Maximum allowed percentage difference
    
    Returns:
        bool: True if validation passes
    """
    base_dir = Path('../../data/precipitation/processed')
    seasonal_dir = base_dir / 'seasonal'
    monthly_dir = base_dir / 'monthly'
    
    print("="*60)
    print("Seasonal-Monthly Validation")
    print("="*60)
    print(f"Year range: {year_range}")
    print(f"Tolerance: {tolerance}%\n")
    
    all_valid = True
    
    for season_code, months in SEASONS.items():
        # Load seasonal file
        seasonal_file = seasonal_dir / f'precip_final_30m_{year_range}_{season_code}.tif'
        
        if not seasonal_file.exists():
            print(f"❌ {season_code.upper()}: Seasonal file not found: {seasonal_file}")
            all_valid = False
            continue
        
        seasonal_data = load_raster(seasonal_file)
        
        # Load and sum monthly files
        monthly_sum = None
        missing_months = []
        
        for month in months:
            monthly_file = monthly_dir / f'precip_final_30m_{year_range}_{month:02d}.tif'
            
            if not monthly_file.exists():
                missing_months.append(month)
                continue
            
            monthly_data = load_raster(monthly_file)
            
            if monthly_sum is None:
                monthly_sum = monthly_data.copy()
            else:
                monthly_sum += monthly_data
        
        if missing_months:
            print(f"❌ {season_code.upper()}: Missing monthly files for months {missing_months}")
            all_valid = False
            continue
        
        # Compare seasonal vs sum of monthly
        # Use only valid (non-masked) pixels for comparison
        valid_mask = ~seasonal_data.mask & ~monthly_sum.mask
        
        if not np.any(valid_mask):
            print(f"❌ {season_code.upper()}: No valid pixels to compare")
            all_valid = False
            continue
        
        seasonal_valid = seasonal_data[valid_mask]
        monthly_valid = monthly_sum[valid_mask]
        
        # Calculate difference
        diff = np.abs(seasonal_valid - monthly_valid)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        # Calculate percentage difference
        mean_seasonal = np.mean(seasonal_valid)
        pct_diff = (mean_diff / mean_seasonal * 100) if mean_seasonal > 0 else 0
        
        # Check if within tolerance
        passed = pct_diff <= tolerance
        
        status = "✅" if passed else "❌"
        print(f"{status} {season_code.upper()} (months {months}):")
        print(f"   Seasonal mean: {mean_seasonal:.2f} mm")
        print(f"   Monthly sum mean: {np.mean(monthly_valid):.2f} mm")
        print(f"   Mean difference: {mean_diff:.2f} mm ({pct_diff:.3f}%)")
        print(f"   Max difference: {max_diff:.2f} mm")
        print(f"   Valid pixels: {np.sum(valid_mask)}")
        
        if not passed:
            all_valid = False
        
        print()
    
    print("="*60)
    if all_valid:
        print("✅ VALIDATION PASSED: Seasonal and monthly data are consistent")
    else:
        print("❌ VALIDATION FAILED: Discrepancies found between seasonal and monthly")
    print("="*60)
    
    return all_valid


if __name__ == '__main__':
    import sys
    
    # Get year range from command line or use default
    year_range = sys.argv[1] if len(sys.argv) > 1 else '2015-2025'
    
    success = validate_seasonal_monthly(year_range)
    sys.exit(0 if success else 1)
