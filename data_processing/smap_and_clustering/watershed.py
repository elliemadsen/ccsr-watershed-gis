import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.patches as patches
import json
from shapely.ops import unary_union

class Watershed():
    def __init__(self, subbasins="data/Subbasins.shp", region="region.geojson", reproject=False):
        self.subbasins = gpd.read_file(subbasins).sort_values('Subbasin')
        if reproject:
            self.subbasins = self.subbasins.to_crs('4326')
        self.outer = unary_union(self.get_geometries())

    def get_geometries(self):
        return self.subbasins["geometry"]

    def get_field(self, field):
        return self.subbasins[field].to_numpy()
    
    def get_lats(self):
        return self.get_field("Lat")

    def get_lons(self):
        return self.get_field("Long_")

    def colormesh(self, lons, lats, values, ax=None, clip=True, vmin=None, vmax=None):
        new_ax = ax is None
        if new_ax:
            fig, ax = plt.subplots()
        im = ax.pcolormesh(lons, lats, values, vmin=vmin, vmax=vmax)
        self.subbasins.plot(ax=ax,color='none', edgecolor="black",linewidth=0.4)
        if clip:
            polygon_patch = patches.Polygon(np.array(self.outer.exterior.xy).transpose(), transform=ax.transData)
            im.set_clip_path(polygon_patch)

        if new_ax:
            plt.show()
        return im

    def plot_labels(self):
        fig, ax = plt.subplots()
        self.subbasins.plot(ax=ax,color='none', edgecolor="black",linewidth=0.4)
        lats = self.get_lats()
        lons = self.get_lons()
        ids = self.get_field('Subbasin')
        for id_str, lat, lon in zip(ids, lats, lons):
            ax.text(lon, lat, str(id_str), color='blue')
        plt.show()

    def grid_to_csv(self, path):
        subbasins_x = self.get_lons()
        subbasins_y = self.get_lats()
        subbasins_name = self.get_field('Subbasin')
        basins = np.zeros((subbasins_name.size, 3))
        basins[:, 0] = subbasins_name
        basins[:, 1] = subbasins_y
        basins[:, 2] = subbasins_x
        np.savetxt(path, basins, fmt='%d,%.8f,%.8f', delimiter=',', header='Subbasin,Lat,Long')

if __name__ == '__main__':
    watershed = Watershed()
    # watershed.plot_labels()
    watershed.grid_to_csv('test.csv')