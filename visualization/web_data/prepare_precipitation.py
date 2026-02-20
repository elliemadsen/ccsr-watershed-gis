"""
Convert monthly precipitation data to JSON for Three.js visualization.
Includes Voronoi cell geometries for spatial interpolation.
"""
import sys
sys.path.insert(0, '..')

import pandas as pd
import numpy as np
import json
import glob
import re
from scipy.spatial import Voronoi
from pathlib import Path

def parse_grid_coords(column_name):
    """Parse '(42.125, -75.125)' to [lat, lon]."""
    match = re.search(r'\(([-\d.]+),\s*([-\d.]+)\)', column_name)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return [lat, lon]
    return None

def create_voronoi_cells(centroids):
    """Create Voronoi cells from centroids and return cell boundaries."""
    # Convert lat/lon centroids to array
    points = np.array(centroids)
    
    # Create Voronoi diagram
    vor = Voronoi(points)
    
    # Build cell geometries
    cells = []
    for idx, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        if -1 not in region and len(region) > 0:  # Valid finite region
            vertices = [vor.vertices[i].tolist() for i in region]
            cells.append({
                'centroid': centroids[idx],
                'vertices': vertices
            })
        else:
            # For infinite regions, we'll create a large bounding polygon
            # This is a simplified approach - in production you'd clip to watershed bounds
            cells.append({
                'centroid': centroids[idx],
                'vertices': None  # Will handle in frontend
            })
    
    return cells

def load_monthly_data():
    """Load all monthly precipitation CSV files."""
    pattern = '../../data/climate_models/monthly/Catskills_*_monthly_avg.csv'
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f'No monthly files found matching: {pattern}')
        return None
    
    print(f'Found {len(csv_files)} monthly precipitation files')
    
    # Parse filenames to extract metadata
    datasets = {}
    
    for csv_file in sorted(csv_files):
        filename = Path(csv_file).stem
        # Parse: Catskills_[MODEL]_[variable]_[scenario]_monthly_avg
        match = re.match(r'Catskills_(.+?)_(.+?)_(ssp\d+)_monthly_avg', filename)
        if match:
            model = match.group(1)
            variable = match.group(2)
            scenario = match.group(3)
            
            dataset_key = f'{model}_{variable}_{scenario}'
            
            # Read CSV
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            
            # Parse grid cell coordinates from column names
            centroids = []
            for col in df.columns:
                coords = parse_grid_coords(col)
                if coords:
                    centroids.append(coords)
            
            # Convert dataframe to time series dict
            time_series = {}
            for date, row in df.iterrows():
                date_str = date.strftime('%Y-%m')
                values = [float(v) if not pd.isna(v) else None for v in row.values]
                time_series[date_str] = values
            
            datasets[dataset_key] = {
                'model': model,
                'variable': variable,
                'scenario': scenario,
                'centroids': centroids,
                'timeSeries': time_series
            }
            
            print(f'  Loaded: {dataset_key}')
    
    return datasets

def get_dem_bounds():
    """Get DEM bounds for reference from existing dem_data.json."""
    dem_json_path = 'dem_data.json'
    try:
        with open(dem_json_path, 'r') as f:
            dem_data = json.load(f)
        return dem_data['bounds']
    except FileNotFoundError:
        print(f'Warning: {dem_json_path} not found, using default bounds')
        return {
            'minX': 0,
            'maxX': 0,
            'minY': 0,
            'maxY': 0
        }

def main():
    print('Preparing precipitation data for Three.js...\n')
    
    # Load all monthly data
    datasets = load_monthly_data()
    
    if not datasets:
        print('No data to process!')
        return
    
    # Get first dataset to extract centroids (all should have same centroids)
    first_dataset = next(iter(datasets.values()))
    centroids = first_dataset['centroids']
    
    print(f'\nGrid cells (centroids):')
    for i, centroid in enumerate(centroids):
        print(f'  Cell {i}: lat={centroid[0]}, lon={centroid[1]}')
    
    # Create Voronoi cells
    print('\nCreating Voronoi cells...')
    voronoi_cells = create_voronoi_cells(centroids)
    
    # Get DEM bounds for reference
    dem_bounds = get_dem_bounds()
    print(f'\nDEM bounds: {dem_bounds}')
    
    # Get time range from first dataset
    time_keys = sorted(next(iter(datasets.values()))['timeSeries'].keys())
    time_range = {
        'start': time_keys[0],
        'end': time_keys[-1],
        'count': len(time_keys)
    }
    
    print(f'\nTime range: {time_range["start"]} to {time_range["end"]} ({time_range["count"]} months)')
    
    # Prepare output
    output = {
        'centroids': centroids,
        'voronoiCells': voronoi_cells,
        'demBounds': dem_bounds,
        'timeRange': time_range,
        'datasets': datasets
    }
    
    # Save to JSON
    output_path = 'precipitation_data.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    file_size = len(json.dumps(output)) / (1024 * 1024)
    print(f'\nSaved to {output_path}')
    print(f'File size: {file_size:.2f} MB')
    
    print('\nDatasets available:')
    for key in sorted(datasets.keys()):
        print(f'  - {key}')

if __name__ == '__main__':
    main()
