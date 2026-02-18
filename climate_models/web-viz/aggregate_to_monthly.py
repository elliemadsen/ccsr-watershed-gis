"""
Aggregate daily precipitation data to monthly averages.
Creates new CSV files with naming: Catskills_[MODEL]_[variable]_[scenario]_monthly_avg.csv
"""
import pandas as pd
import glob
import os
from pathlib import Path

def aggregate_daily_to_monthly(input_file):
    """Aggregate a daily CSV file to monthly averages."""
    print(f'Processing: {input_file}')
    
    # Read the CSV
    df = pd.read_csv(input_file, index_col=0, parse_dates=True)
    
    # Get the date range
    print(f'  Date range: {df.index[0]} to {df.index[-1]}')
    print(f'  Grid cells: {len(df.columns)}')
    
    # Resample to monthly averages
    monthly_df = df.resample('MS').mean()  # 'MS' = Month Start
    
    print(f'  Monthly records: {len(monthly_df)}')
    
    # Create output filename
    input_path = Path(input_file)
    output_filename = input_path.stem.replace('_daily_avg', '_monthly_avg') + '.csv'
    output_path = input_path.parent / output_filename
    
    # Save
    monthly_df.to_csv(output_path)
    print(f'  Saved to: {output_path}')
    
    return output_path

def main():
    # Find all daily average CSV files
    pattern = 'Catskills_*_daily_avg.csv'
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f'No files matching pattern: {pattern}')
        return
    
    print(f'Found {len(csv_files)} files to process\n')
    
    for csv_file in sorted(csv_files):
        aggregate_daily_to_monthly(csv_file)
        print()
    
    print('Done!')

if __name__ == '__main__':
    main()
