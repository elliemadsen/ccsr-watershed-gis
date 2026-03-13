import numpy as np
import shapely

def sort_grids(grids, data):
    return sorted(grids, key=lambda grid: data[grid.col, grid.row])

def save_grids(grids, data, file):
    table_text = []
    for grid in grids:
        grid_data = data[:, grid.col, grid.row]
        quantiles = np.quantile(grid_data, [0.0, 0.25, 0.5, 0.75, 1.0])
        stdev = np.std(grid_data)
        grid_data_mean = np.mean(grid_data)
        table_text.append([grid.get_grid_index(), quantiles[0], quantiles[1], quantiles[2], quantiles[3], quantiles[4], grid_data_mean, stdev])
    table_array = np.array(table_text)
    np.savetxt(file, table_array, delimiter=",", header="Index,Min,Q1,Median,Q3,Max,Mean,Std. Dev", fmt=["%d"] +["%.4f" for i in range(7)])   

def grids_to_indices(grids):
    x = []
    y = []
    for grid in grids:
        y.append(grid.col)
        x.append(grid.row)
    return (np.array(y), np.array(x))

def get_winter(times, data):
    winter_indices = np.where((times.astype('datetime64[M]').astype(int) % 12 == 11) | (times.astype('datetime64[M]').astype(int) % 12 == 0) | (times.astype('datetime64[M]').astype(int) % 12 == 1))
    return times[winter_indices], data[winter_indices]

def get_spring(times, data):
    spring_indices = np.where((times.astype('datetime64[M]').astype(int) % 12 == 2) | (times.astype('datetime64[M]').astype(int) % 12 == 3) | (times.astype('datetime64[M]').astype(int) % 12 == 4))
    return times[spring_indices], data[spring_indices]

def get_summer(times, data):
    summer_indices = np.where((times.astype('datetime64[M]').astype(int) % 12 == 5) | (times.astype('datetime64[M]').astype(int) % 12 == 6) | (times.astype('datetime64[M]').astype(int) % 12 == 7))
    return times[summer_indices], data[summer_indices]

def get_autumn(times, data):
    autumn_indices = np.where((times.astype('datetime64[M]').astype(int) % 12 == 8) | (times.astype('datetime64[M]').astype(int) % 12 == 9) | (times.astype('datetime64[M]').astype(int) % 12 == 10))
    return times[autumn_indices], data[autumn_indices]

season_names = ["Winter", "Spring", "Summer", "Autumn"]

class Grid():
    def __init__(self, col, row, lats, lons, lats_dim, lons_dim):
        self.col = col
        self.row = row
        self.lats = lats
        self.lons = lons
        self.lat = lats[col,row]
        self.lon = lons[col,row]
        lon_stride = lons_dim[1] - lons_dim[0]
        lat_stride = lats_dim[1] - lats_dim[0]
        self.box = shapely.box(self.lon - lon_stride / 2, self.lat - lat_stride / 2, self.lon + lon_stride / 2, self.lat + lat_stride / 2)

    def __str__(self):
        return f'Grid({self.col}, {self.row})'
    
    __repr__ = __str__

    def intersect(self, shapely_polygon):
        return shapely.intersection(shapely_polygon, self.box)

    def coverage(self, shapely_polygon):
        intersection = self.intersect(shapely_polygon)
        return intersection.area / self.box.area

    def get_grid_index(self):
        return self.col * self.lats.shape[1] + self.row

class GriddedData():
    def __init__(self, lats, lons, data, transform):
        assert lats.shape == lons.shape
        self.lats = lats
        self.lons = lons
        self.data = data

        self.shape = self.lats.shape
        self.lats_dim = self.lats.flatten()[::self.shape[1]]
        self.lons_dim = self.lons.flatten()[0:self.shape[1]]
        self.transform = transform

    def find_grids(self, condition):
        included = np.zeros(self.shape, dtype=np.bool)

        grids = []
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                grid = Grid(i, j, self.lats, self.lons, self.lats_dim, self.lons_dim)
                if condition(grid):
                    included[grid.col, grid.row] = True
                    grids.append(grid)
        return included, grids

    def get_grid(self, lat, lon):
        row = np.round((lat - self.lats_dim[0]) / (self.lats_dim[1] - self.lats_dim[0])).astype(np.uint64)
        col = np.round((lon - self.lons_dim[0]) / (self.lons_dim[1] - self.lons_dim[0])).astype(np.uint64)
        return row, col

    def interpolate_grid(self, lat, lon):
        row_index = (lat - self.lats_dim[0]) / (self.lats_dim[1] - self.lats_dim[0])
        col_index = (lon - self.lons_dim[0]) / (self.lons_dim[1] - self.lons_dim[0])
        bottom_row_index, bottom_col_index = self.get_grid(lat, lon)

        bottom_left_corner = self.data[bottom_row_index, bottom_col_index]
        bottom_right_corner = self.data[bottom_row_index, bottom_col_index+1]
        top_left_corner = self.data[bottom_row_index+1, bottom_col_index]
        top_right_corner = self.data[bottom_row_index+1, bottom_col_index+1]

        sum1 = (bottom_col_index+1 - col_index)*(bottom_row_index+1 - row_index)*bottom_left_corner
        sum2 = (col_index - bottom_col_index)*(bottom_row_index+1 - row_index)*bottom_right_corner
        sum3 = (bottom_col_index+1 - col_index)*(row_index - bottom_row_index)*top_left_corner
        sum4 = (col_index - bottom_col_index)*(row_index - bottom_row_index)*top_right_corner

        return sum1 + sum2 + sum3 + sum4

class TimeGriddedData(GriddedData):
    def __init__(self, times, lats, lons, data, transform):
        super().__init__(lats, lons, data, transform)
        self.times = times
        assert self.times.shape[0] == self.data.shape[0]

    def get_winter(self):
        return get_winter(self.times, self.data)

    def get_spring(self):
        return get_spring(self.times, self.data)

    def get_summer(self):
        return get_summer(self.times, self.data)

    def get_autumn(self):
        return get_autumn(self.times, self.data)
    
    def get_seasonals(self):
        winter_times, winter_data = self.get_winter()
        spring_times, spring_data = self.get_spring()
        summer_times, summer_data = self.get_summer()
        autumn_times, autumn_data = self.get_autumn()
        return [winter_data, spring_data, summer_data, autumn_data]

    def get_between(self, start_date, end_date):
        indices = np.where((self.times >= start_date) & (self.times < end_date))
        return self.times[indices], self.data[indices]

    def interpolate_grid(self, lat, lon):
        row_index = (lat - self.lats_dim[0]) / (self.lats_dim[1] - self.lats_dim[0])
        col_index = (lon - self.lons_dim[0]) / (self.lons_dim[1] - self.lons_dim[0])
        bottom_row_index, bottom_col_index = self.get_grid(lat, lon)

        bottom_left_corner = self.data[:, bottom_row_index, bottom_col_index]
        bottom_right_corner = self.data[:, bottom_row_index, bottom_col_index+1]
        top_left_corner = self.data[:, bottom_row_index+1, bottom_col_index]
        top_right_corner = self.data[:, bottom_row_index+1, bottom_col_index+1]

        sum1 = (bottom_col_index+1 - col_index)*(bottom_row_index+1 - row_index)*bottom_left_corner
        sum2 = (col_index - bottom_col_index)*(bottom_row_index+1 - row_index)*bottom_right_corner
        sum3 = (bottom_col_index+1 - col_index)*(row_index - bottom_row_index)*top_left_corner
        sum4 = (col_index - bottom_col_index)*(row_index - bottom_row_index)*top_right_corner

        return sum1 + sum2 + sum3 + sum4

# Not gridded, but rather based on the Watershed subbasins
class WatershedData():
    def __init__(self, times, data, lats, lons):
        assert data.shape[0] == times.shape[0]
        self.times = times
        self.data = data
        self.lats = lats
        self.lons = lons
    
    def get_winter(self):
        return get_winter(self.times, self.data)

    def get_spring(self):
        return get_spring(self.times, self.data)

    def get_summer(self):
        return get_summer(self.times, self.data)

    def get_autumn(self):
        return get_autumn(self.times, self.data)

    def get_between(self, start_date, end_date):
        indices = np.where((self.times >= start_date) & (self.times < end_date))
        return self.times[indices], self.data[indices]

    def align_to_watershed(self, watershed):
        watershed_lats = watershed.get_lats()
        watershed_lons = watershed.get_lons()
        watershed_ids = watershed.get_field('Subbasin')

        new_data = np.zeros_like(self.data)
        num_found = 0
        used = []
        for w in range(watershed_ids.size):
            w_lat = watershed_lats[w]
            w_lon = watershed_lons[w]

            lats_diff = self.lats - w_lat
            lons_diff = self.lons - w_lon
            diffs = np.sqrt(np.square(lats_diff) + np.square(lons_diff))
            min_index = np.argmin(diffs)
            new_data[:, watershed_ids[w] - 1] = self.data[:,min_index]
            used.append(w)

        assert np.unique(np.array(used)).size == watershed_ids.size

        self.data = new_data
