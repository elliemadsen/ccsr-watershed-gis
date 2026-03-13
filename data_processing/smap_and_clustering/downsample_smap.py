from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt
import numpy as np
import os
import shapely
import joblib
import xarray as xr
import rasterstats
from rasterio.features import rasterize
import gc

import gridded_data
import datasets
import watershed

# HYPERPARAMETERS
watershed_coverage = 0.5 # Amount of gridcells needed to be in the watershed.
target_grid_size = 30     # Output smap grid size
##
start_month = np.datetime64("2015-04")
half_month = np.datetime64("2020-01")
end_month = np.datetime64("2026-01") # Exclusive
months = np.arange(start_month, end_month)

smap = datasets.read_tif('smap_sm_reproject_9000m_monthly.tif', times=np.arange(np.datetime64("2015-03"), np.datetime64("2026-01")))
ag_mask = datasets.read_tif('natag_mask.tif')

watershed = watershed.Watershed()

class Feature:
    def __init__(self, name, train, monthly, train_cache, predict_djf=None, predict_mam=None, predict_jja=None, predict_son=None):
        self.name = name
        self.train = train
        self.monthly = monthly
        self.train_cache = train_cache
        if predict_djf is None:
            self.predict_djf = train
            self.predict_mam = train
            self.predict_jja = train
            self.predict_son = train
        else:
            self.predict_djf = predict_djf
            self.predict_mam = predict_mam
            self.predict_jja = predict_jja
            self.predict_son = predict_son

# Static Features
dem = Feature(
    "Elevation",
    lambda: datasets.read_tif('DEM_10m_gapfilled.tif'),
    False,
    "elev_features.npy"
)

sand_percent = Feature(
    "Soil: Percent Sand",
    lambda: datasets.read_tif('sand_r_reproject_30m.tif', fill_val=3.4e38),
    False,
    "sand_features.npy"
)

twi = Feature(
    "TWI",
    lambda: datasets.read_tif('TWI_30m.tif'),
    False,
    "twi_features.npy"
)

# Monthly Features
lst = Feature(
    "LST",
    [lambda: datasets.read_tif('lst_reproject_30m_monthly_1.tif'), lambda: datasets.read_tif('lst_reproject_30m_monthly_2.tif')],
    True,
    ["lst_features.npy", "lst_features2.npy"],
    lambda: datasets.read_tif('lst_reproject_30m_djf.tif'),
    lambda: datasets.read_tif('lst_reproject_30m_mam.tif'),
    lambda: datasets.read_tif('lst_reproject_30m_jja.tif'),
    lambda: datasets.read_tif('lst_reproject_30m_son.tif')
)

ndvi = Feature(
    "NDVI",
    [lambda: datasets.read_ndvi_indices(np.arange(3,60)), lambda: datasets.read_ndvi_indices(np.arange(60,132))],
    True,
    ["ndvi_features1.npy", "ndvi_features2.npy"],
    lambda: datasets.read_tif('ndvi_reproject_30m_djf.tif'),
    lambda: datasets.read_tif('ndvi_reproject_30m_mam.tif'),
    lambda: datasets.read_tif('ndvi_reproject_30m_jja.tif'),
    lambda: datasets.read_tif('ndvi_reproject_30m_son.tif')
)

pcp = Feature(
    "Gridmet Precipitation",
    [lambda:  datasets.read_gridmet(start_month, half_month), lambda: datasets.read_gridmet(half_month, end_month)],
    True,
    ["pcp_features.npy", "pcp_features2.npy"],
    lambda: datasets.read_tif('../ccsr-watershed-gis/data/precipitation/processed/seasonal/precip_final_30m_2015-2025_djf.tif'),
    lambda: datasets.read_tif('../ccsr-watershed-gis/data/precipitation/processed/seasonal/precip_final_30m_2015-2025_mam.tif'),
    lambda: datasets.read_tif('../ccsr-watershed-gis/data/precipitation/processed/seasonal/precip_final_30m_2015-2025_jja.tif'),
    lambda: datasets.read_tif('../ccsr-watershed-gis/data/precipitation/processed/seasonal/precip_final_30m_2015-2025_son.tif')
)

features_list = [dem, sand_percent, twi, lst, ndvi, pcp]

def subgrids(grids, step_x=target_grid_size, step_y=target_grid_size):
    # Find min,max x,y across all grids
    # Grid x Bounds. Bounds: min_x, min_y, max_x, max_y
    bounds = np.array([g.box.bounds for g in grids])
    min_x = np.min(bounds[:,0])
    min_y = np.min(bounds[:,1])
    max_x = np.max(bounds[:,2])
    max_y = np.max(bounds[:,3])
    
    # Find final x,y size + centers x,y
    # Start at half step since that should be where the top left grid center is
    centers_x = np.arange(min_x + step_x / 2, max_x, step_x)
    centers_y = np.flip(np.arange(min_y + step_y / 2, max_y, step_y))
    return centers_x, centers_y

_, grids = smap.find_grids(lambda grid: grid.coverage(watershed.outer) > watershed_coverage)

def create_dataset_mask(dataset, mask=ag_mask, plot=False):
    lats = dataset.lats
    lons = dataset.lons
    mask_row, mask_col = mask.get_grid(lats, lons)
    mask_nan = np.where(mask.data == 1, mask.data, np.nan) # Turn the mask into 1 and nan
    masked_data = dataset.data * np.where((mask_row >= 0) & (mask_col >= 0) & (mask_row < mask.shape[0]) & (mask_col < mask.shape[1]), mask_nan[mask_row, mask_col], np.nan)

    if plot:
        fig, axs = plt.subplots(2)

        if len(dataset.data.shape) == 2:
            watershed.colormesh(lons, lats, dataset, ax=axs[0])
            watershed.colormesh(lons, lats, masked_data, ax=axs[1])
        else:
            watershed.colormesh(lons, lats, np.mean(dataset.data, axis=0), ax=axs[0])
            watershed.colormesh(lons, lats, np.mean(masked_data, axis=0), ax=axs[1])
        plt.show()
    return masked_data


# For each feature, find the subgrids that correspond to the SMAP grids. We want to use vectorized operations rather than rely on looping shapely intersection because it's slow
# We also only want to take subgrids that are in the watershed, so those are filtered first.
# It will be of the form: Time x Grids.
def compute_feature(feature_data, grids, area_weights=True):
    if len(feature_data.data.shape) == 3:
        num_months = feature_data.data.shape[0]
    else:
        num_months = months.size

    features = np.zeros((num_months, len(grids)))
    masked_data = create_dataset_mask(feature_data)

    boxes = [g.box for g in grids]
    watershed_boxes = shapely.intersection(watershed.outer, boxes)

    if len(feature_data.data.shape) == 3:
        for t in range(masked_data.shape[0]):
            # zonal stats only allows for 2D means, so have to iterate through time
            stats = rasterstats.zonal_stats(watershed_boxes, masked_data[t], nodata=np.nan, stats=['mean'], affine=feature_data.transform)
            means = np.array([s['mean'] for s in stats])
            features[t, :] = means
    else:
        stats = rasterstats.zonal_stats(watershed_boxes, masked_data, nodata=np.nan, stats=['mean'], affine=feature_data.transform)
        means = np.array([s['mean'] for s in stats])
        features[:] = means

    return features

def get_feature(grids, load_fn, cache):
    if cache is not None and os.path.exists(cache):
        features = np.load(cache)
        if features.shape[-1] == len(grids):
            return features
        # Features were likely computed on different grid coverage if not equal, so reload.
        print("Saved features have different size than number of grids. Likely computed on different grid coverage. Recomputing")
    
    data = load_fn()
    features = compute_feature(data, grids)
    if cache is not None:
        np.save(cache, features)
    return features

feature_vals = []
print("Computing Features")
for feature in features_list:
    print(f'Getting {feature.name} Features')
    if (isinstance(feature.train, list)):
        feature_array = []
        for train_data, cache in zip(feature.train, feature.train_cache):
            train_feature = get_feature(grids, train_data, cache=cache)
            feature_array.append(train_feature)
        feature_val = feature_array[0]
        for val in feature_array[1:]:
            feature_val = np.append(feature_val, val, axis=0)
        feature_vals.append(feature_val)
    else:
        train_feature = get_feature(grids, feature.train, cache=feature.train_cache)
        feature_vals.append(train_feature)
    print(f'Feature shape is {feature_vals[-1].shape}')

def create_random_forest(X, y, groups):
    random_forest = RandomForestRegressor(n_estimators=100, random_state=0)

    logo = LeaveOneGroupOut()
    y_pred = cross_val_predict(
        random_forest,
        X,
        y,
        cv=logo,
        groups=groups,
        n_jobs=-1 # Use all processors
    )

    print("R²:", r2_score(y, y_pred))
    print("RMSE:", mean_squared_error(y, y_pred))

    random_forest.fit(X, y)
    return random_forest

def build_X_y(grids, month_indices, total_features):
    season_months = months[month_indices]
    # SMAP should be monthly grids of coverage >0.5. Time x Grid flattened
    smap_indices = gridded_data.grids_to_indices(grids)
    sm = np.zeros((season_months.size, len(grids)))
    i = 0
    for month in season_months:
        # We do this because the SMAP data starts with 2015-03, of which there was a single point, so this fixes the indices and excludes that month
        indices = np.where(smap.times.astype("datetime64[M]") == month)
        smap_data = smap.data[indices,smap_indices[0], smap_indices[1]]
        sm[i] = smap_data
        i += 1

    # Groups for LeaveOneGroupOut cross_val 
    group_vals = np.arange(1, len(grids) + 1)
    group_vals = np.tile(group_vals, (season_months.size, 1))
    assert group_vals.shape == sm.shape

    group_vals = group_vals.flatten()
    sm = sm.flatten()

    features = [] # X

    for feature in total_features:
        feature_season = feature[month_indices, :].flatten()
        features.append(feature_season)

    # # Transpose in order to be in the correct format (samples x features)
    features = np.array(features).transpose()
    return features, sm, group_vals # X, y, groups

def plot_feature_importances(forest, X, y, title):
    import pandas as pd
    feature_names = [feature.name for feature in features_list]   
    # std = np.std([tree.feature_importances_ for tree in forest.estimators_], axis=0)

    result = permutation_importance(forest, X, y, n_repeats=10, random_state=0)

    forest_importances = pd.Series(result.importances_mean, index=feature_names)
    fig, ax = plt.subplots()
    forest_importances.plot.bar(yerr=result.importances_std, ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Mean decrease in impurity")
    fig.tight_layout()
    plt.show()


def train_season(grids, month_indices, total_features, title, cache=None):
    if cache is not None and os.path.exists(cache):
        forest = joblib.load(cache)
        features, sm, group_vals = build_X_y(grids, month_indices, total_features)
    else:
        features, sm, group_vals = build_X_y(grids, month_indices, total_features)
        # Train
        forest = create_random_forest(features, sm, group_vals)
        if cache is not None:
            joblib.dump(forest, cache)

    plot_feature_importances(forest, features, sm, title)
    return forest

###############################
####### Prediction ############
###############################

def prediction_features(smap_x, smap_y, datalist):
    features = []
    i = 0
    for d in datalist:
        dataset = d()
        i+=1

        d_y, d_x = dataset.get_grid(smap_y, smap_x)
        
        # Some datasets are clipped differently to bounds, so we use closest value
        d_y = np.clip(d_y, a_min=0, a_max=dataset.data.shape[0]-1)
        d_x = np.clip(d_x, a_min=0, a_max=dataset.data.shape[1]-1)

        d_features = dataset.data[d_y, d_x]
        features.append(d_features)
    return np.array(features).transpose()

def compute_grid_mask(use_mask=True):
    if use_mask:
        # Just take ag mask lat/lons
        indices = np.where(ag_mask.data == 1)
        smap_x = ag_mask.lons[indices]
        smap_y = ag_mask.lats[indices]
        return smap_x, smap_y, ag_mask.lons_dim, ag_mask.lats_dim, indices
    else:
        # # Create smap subgrids based on the mask
        _, all_grids = smap.find_grids(lambda grid: True)
        centers_x, centers_y = subgrids(all_grids)
        lons_grid, lats_grid = np.meshgrid(centers_x, centers_y)
        mask_row, mask_col = ag_mask.get_grid(lats_grid, lons_grid)
        index_mask = np.where((mask_row >= 0) & (mask_col >= 0) & (mask_row < mask.shape[0]) & (mask_col < mask.shape[1]), ag_mask.data[mask_row, mask_col], 0)
        indices = np.where(index_mask == 1)

        smap_x = lons_grid[indices]
        smap_y = lats_grid[indices]

        return smap_x, smap_y, centers_x, centers_y, indices

def predict(forest, features):
    return forest.predict(features)

def convert_prediction_to_raster(indices, centers_x, centers_y, predictions):
    lons_grid, lats_grid = np.meshgrid(centers_x, centers_y)
    raster = np.empty_like(lons_grid)
    raster[:] = np.nan

    raster[indices] = predictions
    return raster

def constrain_spatial_mean(raster_file, smap_9km):
    # Constrain spatial mean for all grids that have any coverage. We are assuming the monthly grids are the same as the seasonals
    _, grids = smap_9km.find_grids(lambda grid: grid.coverage(watershed.outer) > 0)

    boxes = [g.box for g in grids]
    watershed_boxes = shapely.intersection(watershed.outer, boxes)
    row, col = gridded_data.grids_to_indices(grids)
    constraining_pixel_values = smap_9km.data[row, col]

    # Assign a unique value per feature
    shapes = [(geom, i+1) for i, geom in enumerate(watershed_boxes)]

    raster = datasets.read_tif(raster_file)

    # Generate mask over raster where each raster pixel determines which geometry it is in.
    mask = rasterize(
        shapes=shapes,
        out_shape=raster.shape,
        transform=raster.transform,
        fill=0,              # value for pixels not in any feature
        dtype="int32"
    )

    adj_data = raster.data.copy()
    # Now we need to find which downsampled pixels are in which original smap pixel
    a = []
    for shape in shapes:
        geom = shape[0]
        index = shape[1]
        indices = np.where(mask == index)
        region_mask = np.empty_like(mask).astype(np.float64)
        region_mask[:] = np.nan
        region_mask[indices] = 1
        pixel_mean = np.nanmean(region_mask * raster.data)
        a.append(pixel_mean)
        adj_data[indices] = raster.data[indices] * (constraining_pixel_values[index-1] / pixel_mean)

    # @TODO: Check to see if these match the pixel means
    # stats = rasterstats.zonal_stats(watershed_boxes, raster_file, stats=['mean'])
    # pixel_means = np.array([s['mean'] for s in stats])
    # print(pixel_means)

    print(adj_data.shape)

    raster_adj = xr.DataArray(
        data=adj_data,
        dims=["y","x"],
        coords=dict(
            x=raster.lons_dim,
            y=raster.lats_dim
        )
    )
    raster_adj.rio.to_raster(raster_file.replace('downscaled', 'constrained'))


def predict_raster(forest, smap_x, smap_y, centers_x, centers_y, indices, data_list, file):
    features_predict = prediction_features(smap_x, smap_y, data_list)
    predictions_flat = predict(forest, features_predict)
    raster = convert_prediction_to_raster(indices, centers_x, centers_y, predictions_flat)
    raster_xr = xr.DataArray(
        data=raster,
        dims=["y","x"],
        coords=dict(
            x=centers_x,
            y=centers_y
        )
    )
    raster_xr.rio.to_raster(file)


print("Training DJF")
djf_forest = train_season(grids, np.where((months.astype(int) % 12 == 11) | (months.astype(int) % 12 == 0) | (months.astype(int) % 12 == 1)), feature_vals, "DJF", "forest_djf.joblib")
print("Training MAM")
mam_forest = train_season(grids, np.where((months.astype(int) % 12 == 2) | (months.astype(int) % 12 == 3) | (months.astype(int) % 12 == 4)), feature_vals, "MAM", "forest_mam.joblib")
print("Training JJA")
jja_forest = train_season(grids, np.where((months.astype(int) % 12 == 5) | (months.astype(int) % 12 == 6) | (months.astype(int) % 12 == 7)), feature_vals, "JJA", "forest_jja.joblib")
print("Training SON")
son_forest = train_season(grids, np.where((months.astype(int) % 12 == 8) | (months.astype(int) % 12 == 9) | (months.astype(int) % 12 == 10)), feature_vals, "SON", "forest_son.joblib")

def create_seasonal_predictions():
    smap_x, smap_y, centers_x, centers_y, indices = compute_grid_mask()

    print("Predicting DJF")
    winter_list = [feature.predict_djf for feature in features_list]
    predict_raster(djf_forest, smap_x, smap_y, centers_x, centers_y, indices, winter_list, 'smap_sm_downscaled_30m_djf.tif')
    constrain_spatial_mean('smap_sm_downscaled_30m_djf.tif', datasets.read_tif('smap_sm_reproject_9000m_djf.tif'))

    print("Predicting MAM")
    mam_list = [feature.predict_mam for feature in features_list]
    predict_raster(mam_forest, smap_x, smap_y, centers_x, centers_y, indices, mam_list, 'smap_sm_downscaled_30m_mam.tif')
    constrain_spatial_mean('smap_sm_downscaled_30m_mam.tif', datasets.read_tif('smap_sm_reproject_9000m_mam.tif'))

    print("Predicting JJA")
    jja_list = [feature.predict_jja for feature in features_list]
    predict_raster(jja_forest, smap_x, smap_y, centers_x, centers_y, indices, jja_list, 'smap_sm_downscaled_30m_jja.tif')
    constrain_spatial_mean('smap_sm_downscaled_30m_jja.tif', datasets.read_tif('smap_sm_reproject_9000m_jja.tif'))

    print("Predicting SON")
    son_list = [feature.predict_son for feature in features_list]
    predict_raster(son_forest, smap_x, smap_y, centers_x, centers_y, indices, son_list, 'smap_sm_downscaled_30m_son.tif')
    constrain_spatial_mean('smap_sm_downscaled_30m_son.tif', datasets.read_tif('smap_sm_reproject_9000m_son.tif'))

create_seasonal_predictions()
