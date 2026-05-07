import watershed
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
import datasets
import gridded_data
import rasterstats
import rioxarray
import shapely
from rasterio.features import rasterize, geometry_mask

watershed = watershed.Watershed()
 
subbasins_x = watershed.get_lons()
subbasins_y = watershed.get_lats()

ag_mask = datasets.read_tif('natag_mask.tif')

np.random.seed(0)

### 
### Step 1: Isolate small subbasins
###
def find_small_subbasins(ws=watershed):
    watershed_geometries = ws.get_geometries()
    stats = rasterstats.zonal_stats(watershed_geometries, 'natag_mask.tif', nodata=0, stats=['count'])
    counts = np.zeros_like(subbasins_x)
    for i in range(len(stats)):
        counts[i] = stats[i]['count']

    q25, q75 = np.quantile(np.log(counts), [.25,.75])
    iqr = q75-q25
    low = q25 - 1.5*iqr

    # Small indices are outliers on log scale.
    small_indices = np.where(counts < np.exp(low))[0]
    return small_indices

ignore_indices = find_small_subbasins()
print(f"Ignoring subbasins {[int(i + 1) for i in ignore_indices]} for clustering since they are too small")
subbasins_num = subbasins_x.size - len(ignore_indices) # For training KMeans

### 
### Step 2: Compute features
###
def get_mean_std(data):
    return np.mean(data, axis=1), np.std(data, axis=1)

def normalize(item):
    if len(item.shape) > 1:
        scaler = StandardScaler().fit(item)
        return scaler.transform(item)
    else:
        scaler = StandardScaler().fit(item.reshape(-1, 1))
        return scaler.transform(item.reshape(-1, 1)).flatten()

def fit(array, n_clusters=8):
    kmeans = KMeans(n_clusters=n_clusters, n_init=25, random_state=0).fit(array)
    return array, kmeans

def compute_features(to_fit, weights=None):
    if weights is None:
        weights = []
    params_size = 0

    is_empty = len(weights) == 0
    expected_shape = to_fit[0].shape[0]
    for item in to_fit:
        assert item.shape[0] == expected_shape # Make sure they are all the same shape
        if len(item.shape) == 1:
            params_size += 1
        else:
            params_size += item.shape[1]
        if is_empty:
            weights.append(1)

    array = np.zeros((expected_shape, params_size))
    index_counter = 0

    assert len(to_fit) == len(weights)

    weights = np.array(weights)
    # Normalize weights to add to one. I don't think we should do this. The output just needs to understand how many weights there were.
    # weights = weights / np.sum(weights)

    for item, weight in zip(to_fit, weights):
        item_size = 1
        if len(item.shape) > 1:
            item_size = item.shape[1]
            scaler = StandardScaler().fit(item)
            array[:,index_counter:index_counter+item_size] = scaler.transform(item) * weight
            index_counter += item_size
        else:
            scaler = StandardScaler().fit(item.reshape(-1, 1))
            array[:,index_counter] = scaler.transform(item.reshape(-1, 1)).flatten() * weight
            index_counter += 1
    return array

def fit_list(to_fit, n_clusters=8, weights=None):
    array = compute_features(to_fit, weights=weights)
    return fit(array, n_clusters)

def pad_labels(kmeans, indices_to_insert, pad_values):
    labels = kmeans.labels_.tolist()
    for index, val in zip(indices_to_insert, pad_values):
        labels.insert(index, val)
    return np.array(labels)

def plot_kmeans(labels, fig, ax, cmap = mpl.cm.jet):
    watershed.subbasins.plot(ax=ax, column=labels, edgecolor="black",linewidth=0.4, legend=False, cmap=cmap)
    n_clusters = np.max(labels) + 1
    bounds = np.linspace(0, n_clusters, n_clusters + 1)
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)

def create_dataset_mask(dataset, mask=ag_mask):
    lats = dataset.lats
    lons = dataset.lons
    mask_row, mask_col = mask.get_grid(lats, lons)
    mask_nan = np.where(mask.data == 1, mask.data, np.nan) # Turn the mask into 1 and nan

    # Some datasets are clipped differently to bounds, so we use closest value
    mask_row = np.clip(mask_row, a_min=0, a_max=mask.data.shape[0]-1)
    mask_col = np.clip(mask_col, a_min=0, a_max=mask.data.shape[1]-1)

    masked_data = dataset.data * np.where((mask_row >= 0) & (mask_col >= 0) & (mask_row < mask.shape[0]) & (mask_col < mask.shape[1]), mask_nan[mask_row, mask_col], np.nan)
    return masked_data

def compute_mean_std(tif_path, ws=watershed, mask=True):
    watershed_geometries = ws.get_geometries()
    means = np.zeros_like(subbasins_x)
    stds = np.zeros_like(subbasins_x)
    counts = np.zeros_like(subbasins_x)

    if mask:
        dataset = datasets.read_tif(tif_path)
        masked_data = create_dataset_mask(dataset)
        stats = rasterstats.zonal_stats(watershed_geometries, masked_data, nodata=np.nan, stats=['mean', 'std', 'count'], affine=dataset.transform)
    else:
        stats = rasterstats.zonal_stats(watershed_geometries, tif_path, nodata=np.nan, stats=['mean', 'std', 'count'])
    for i in range(len(stats)):
        means[i] = stats[i]['mean']
        stds[i] = stats[i]['std']
        counts[i] = stats[i]['count']
        # print(f'{i}:{stats[i]['count']}')

    return means, stds

class ClusterInput():
    def __init__(self, path, mask=True, use_mean=True, use_std=False):
        self.path = path
        self.mask = mask
        self.use_mean = use_mean
        self.use_std = use_std

### 
### Here is where we define our inputs
###

# These are already masked, so don't need to mask them.
smap_djf = ClusterInput('smap_sm_constrained_30m_djf.tif', False)
smap_mam = ClusterInput('smap_sm_constrained_30m_mam.tif', False)
smap_jja = ClusterInput('smap_sm_constrained_30m_jja.tif', False)
smap_son = ClusterInput('smap_sm_constrained_30m_son.tif', False)

pcp_djf = ClusterInput('../../data/precipitation/processed/seasonal/precip_final_30m_2015-2025_djf.tif')
pcp_mam = ClusterInput('../../data/precipitation/processed/seasonal/precip_final_30m_2015-2025_mam.tif')
pcp_jja = ClusterInput('../../data/precipitation/processed/seasonal/precip_final_30m_2015-2025_jja.tif')
pcp_son = ClusterInput('../../data/precipitation/processed/seasonal/precip_final_30m_2015-2025_son.tif')

runoff_coef = ClusterInput('runoff_curve_number.tif', False)

stream_distance = ClusterInput('../../data/stream_proximity/stream_distance/stream_distance_25ha.tif')
restrict_depth = ClusterInput('depth_restrictive_30m.tif')

twi = ClusterInput('TWI_30m.tif', use_std=True)

cluster_inputs = [
    smap_djf, smap_mam, smap_jja, smap_son,
    pcp_djf, pcp_mam, pcp_jja, pcp_son,
    runoff_coef, stream_distance, restrict_depth, twi
]

### 
### Step 3: Clustering
###
# Higher is better
def kmeans_silhouette_coefficient(array, kmeans):
    from sklearn import metrics
    return metrics.silhouette_score(array, kmeans.labels_, metric='euclidean')

# Higher is better
def kmeans_calinski_harabasz_score(array, kmeans):
    from sklearn import metrics
    return metrics.calinski_harabasz_score(array, kmeans.labels_)

# 'similarity' between clusters. Lower is better
def kmeans_davies_bouldin_score(array, kmeans):
    from sklearn import metrics
    return metrics.davies_bouldin_score(array, kmeans.labels_)

# Lower is better
def kmeans_inertia(array, kmeans):
    return kmeans.inertia_

def gap_stat(array, k):
    def generate_reference_data(X):
        return np.random.uniform(low=X.min(axis=0), high=X.max(axis=0), size=X.shape)

    _, kmeans = fit(array, k)
    original_inertia = kmeans.inertia_

    reference_inertia = []
    n_references = 100
    for _ in range(n_references):
        random_data = generate_reference_data(array)
        kmeans.fit(random_data)
        reference_inertia.append(np.log(kmeans.inertia_))

    log_ref_mean = np.mean(reference_inertia)
    std = np.std(reference_inertia)
    std_error = std * np.sqrt(1 + 1 / n_references)

    gap = log_ref_mean - np.log(original_inertia)
    return gap, std_error

def plot_clusters(list_to_fit, weights=None):
    if weights is None:
        weights = []
    n_clusters = [i for i in range(2,9)]
    inertias = []
    silhouette_scores = []
    calinski_harabasz_scores = []
    davies_bouldin_scores = []
    gap_stats = []
    std_errors = []

    kmeanses = []

    for i in range(len(n_clusters)):
        array, kmeans = fit_list(list_to_fit, n_clusters[i], weights=weights.copy())
        inertias.append(kmeans_inertia(array, kmeans))
        silhouette_scores.append(kmeans_silhouette_coefficient(array, kmeans))
        gap, se = gap_stat(array, n_clusters[i])
        gap_stats.append(gap)
        std_errors.append(se)
        kmeanses.append(kmeans)

    best_k = None
    for i in range(len(n_clusters)-1):
        if gap_stats[i] >= gap_stats[i + 1] - std_errors[i + 1]:
            best_k = n_clusters[i]
            break
    if best_k is None:
        best_k = n_clusters[-1]
    print(f"Best K according to Gap Stat is {best_k}")

    total_weights = np.sum(weights)
    if total_weights == 0:
        total_weights = len(list_to_fit)

    fig, axs = plt.subplots(2)
    axs[0].plot(n_clusters, silhouette_scores)
    axs[0].set_title("Silhouette Score")
    axs[1].plot(n_clusters, gap_stats)
    axs[1].set_title("Gap Statistics")
    plt.show()
    return kmeanses

def mean_over_indices(indices, data):
    data_sub = np.squeeze(data[:, indices])
    return np.mean(data_sub, axis=1), np.std(data_sub, axis=1)

def perform_clustering(input_clusters, ignore_indices, plot_metrics=True, plot=True):
    list_to_fit = []
    for input_cluster in input_clusters:
        computed_mean, computed_std = compute_mean_std(input_cluster.path, mask=input_cluster.mask)
        if input_cluster.use_mean:
            list_to_fit.append(computed_mean)
        if input_cluster.use_std:
            list_to_fit.append(computed_std)

    ignored_list = [arr[ignore_indices] for arr in list_to_fit]
    list_to_fit_excluded = [np.delete(arr, ignore_indices) for arr in list_to_fit]

    # For each input data, remove the indices that should be removed
    weights = [1,1,1,1, 1,1,1,1, 4, 4, 4, 2, 2]

    if plot_metrics:
        plot_clusters(list_to_fit_excluded)
        # plot_clusters(list_to_fit_excluded, weights)

    # Re-fit
    _, kmeans = fit_list(list_to_fit_excluded, 6)
    # _, kmeans = fit_list(list_to_fit_excluded, 7)
    # plot_2_clusters(kmeans11, "5 Clusters", kmeans12, "7 Clusters")


    # Re-fit
    # _, kmeans = fit_list(list_to_fit_excluded, 5, weights)
    # _, kmeans = fit_list(list_to_fit_excluded, 7, weights)
    # plot_2_clusters(kmeans21, "3 Clusters", kmeans22, "7 Clusters")

    # After fitting, compute labels for ignored subbasins
    features = compute_features(ignored_list)
    new_labels = kmeans.predict(features)
    labels = pad_labels(kmeans, ignore_indices, new_labels)

    if plot:
        fig, ax = plt.subplots()
        plot_kmeans(labels, fig, ax)
        plt.show()

    return kmeans, labels

kmeans, labels = perform_clustering(cluster_inputs, ignore_indices)

### 
### Step 4: Compute profiles
###
def write_shapefile(labels, indices_to_insert, file):
    watershed.subbasins["clusters"] = labels
    watershed.subbasins.to_file(file)

num_clusters = np.max(labels) + 1
write_shapefile(labels, ignore_indices, f'watershed_clusters{num_clusters}.shp')

def compute_cluster_profiles(cluster_inputs, labels, ignore_indices):
    watershed_geometries = watershed.get_geometries()

    def cluster_mask_raster(raster_path, plot=False):
        raster = datasets.read_tif(raster_path)

        mask = np.full(raster.shape, np.nan)
        
        for geom, label in zip(watershed_geometries, labels):
            # Create a mask for this geometry
            if label >= 0:
                indices = geometry_mask(
                    [geom],
                    out_shape=raster.shape,
                    transform=raster.transform,
                    invert=True  # True = pixels INSIDE the geometry
                )
                mask[indices] = label

        if plot:
            fig, ax = plt.subplots()
            im = ax.pcolormesh(raster.lons_dim, raster.lats_dim, mask)
            fig.colorbar(im, ax=ax)
            plt.show()

        return raster, mask

    num_clusters = np.max(labels) + 1
    profiles = np.zeros((num_clusters, len(cluster_inputs) * 2 + 11)) # Mean/Std of cluster inputs + CDL categories
    profile_i = 0

    for cluster_input in cluster_inputs:
        raster, mask = cluster_mask_raster(cluster_input.path)
        max_val = int(np.nanmax(mask))
        for i in range(max_val+1):
            indices = np.where(mask == i)
            region_mask = np.empty_like(mask).astype(np.float64)
            region_mask[:] = np.nan
            region_mask[indices] = 1

            if cluster_input.mask:
                masked_data = create_dataset_mask(raster)            
            else:
                masked_data = raster.data
            pixel_mean = np.nanmean(region_mask * masked_data)
            pixel_std = np.nanstd(region_mask * masked_data)

            profiles[i, 2 * profile_i] = pixel_mean
            profiles[i, 2 * profile_i + 1] = pixel_std
            print(f'Input {cluster_input.path}, Cluster {i+1}, Mean: {pixel_mean}, Std: {pixel_std}')
        print()
        profile_i += 1
    
    # Find percentages of each CDL classification as well
    raster, mask = cluster_mask_raster('cdl_2023_classified.tif')

    # From CDL23_Nat-Ag_AssignedCodes.xlsx
    cdl_vals = {
        1: "Forest",
        2: "Wetlands",
        3: "Shrubland",
        4: "Pasture/Grassland",
        5: "Hay",
        6: "Idle",
        7: "Corn",
        8: "Soybeans",
        9: "Double Crop",
        10: "Rye",
        11: "Alfalfa"
    }
    
    max_val = int(np.nanmax(mask))
    for i in range(max_val+1):
        indices = np.where(mask == i)
        region_mask = np.empty_like(mask).astype(np.float64)
        region_mask[:] = np.nan
        region_mask[indices] = 1

        # CDL is already masked
        nan_data = np.where(raster.data == 0, np.nan, raster.data)
        cdl_mask = region_mask * nan_data

        values, counts = np.unique(cdl_mask, return_counts=True)

        # NaN is last
        values = values[:-1]
        counts = counts[:-1]
        counts = counts / np.sum(counts) * 100

        for v, c in zip(values, counts):
            profiles[i, 2 * profile_i + int(v) - 1] = c
            print(f'CDL {cdl_vals[v]}, Cluster {i+1}, Percent: {c}')
        print()
    
    header = 'SMAP DJF Mean, SMAP DJF Std, SMAP MAM Mean, SMAP MAM Std, SMAP JJA Mean, SMAP JJA Std, SMAP SON Mean, SMAP SON Std, '
    header += 'PCP DJF Mean, PCP DJF Std, PCP MAM Mean, PCP MAM Std, PCP JJA Mean, PCP JJA Std, PCP SON Mean, PCP SON Std, '
    header += 'Runoff Mean, Runoff Std, Steam Distance Mean, Stream Distance Std, Depth to Restrictive Layer Mean, Depth to Restrictive Layer Std, '
    header += 'TWI Mean, TWI Std, Forest %, Wetlands %, Shrubland %, Pasture/Grassland %, Hay %, Idle %, Corn %, Soybeans %, Double Crop %, Rye %, Alfalfa %'

    np.savetxt(f'cluster_profiles{num_clusters}.csv', profiles, fmt='%.5f', delimiter=',', header=header)

compute_cluster_profiles(cluster_inputs, labels, ignore_indices)
