import ee, geemap
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

ee.Authenticate()
ee.Initialize(project="gsapp-map")

ckxu = ee.ImageCollection("projects/sat-io/open-datasets/VODCA/CKXU_BAND_V2")

# Catchment bounding boxes [W, S, E, N]
LOCATIONS = {
    "Hinckley_NY":   ee.Geometry.Rectangle([-75.53, 42.78, -74.26, 43.89]), # Hinckley Reservoir (Utica)
    "Cannonsville_NY":  ee.Geometry.Rectangle([-75.54, 41.56, -74.17, 42.62]), # Cannonsville Reservoir (New York City water supply)
    "Sebago_ME":     ee.Geometry.Rectangle([-71.13, 43.35, -69.95, 44.64]), # Sebago Lake (Portland)
    "Alcove_NY":     ee.Geometry.Rectangle([-74.60, 41.85, -73.60, 42.83]), # Alcove Reservoir (Albany)
    "Scituate_RI":   ee.Geometry.Rectangle([-72.14, 40.90, -71.11, 42.16]), # Scituate Reservoir (Providence)
    "Hemlock_NY":    ee.Geometry.Rectangle([-77.97, 42.32, -77.17, 43.28]), # Hemlock Lake (Rochester)
    "Barkhamsted_CT":ee.Geometry.Rectangle([-73.45, 41.38, -72.38, 42.55]), # Barkhamsted Reservoir (Hartford)
    "Quabbin_MA":    ee.Geometry.Rectangle([-72.87, 41.79, -71.64, 42.83]), # Quabbin Reservoir (Boston)
    "Wachusett_MA":  ee.Geometry.Rectangle([-72.22, 42.05, -71.20, 43.08]), # Wachusett Reservoir (Boston)
    "Massabesic_NH": ee.Geometry.Rectangle([-71.92, 42.61, -71.02, 43.36]), # Lake Massabesic (Manchester)
}

def make_extractor(aoi):
    def extract(img):
        mean = img.select('VOD').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=25000, maxPixels=1e6
        )
        return ee.Feature(None, {
            'date': img.date().format('YYYY-MM-dd'),
            'VOD_mean': mean.get('VOD')
        })
    return extract

for name, aoi in LOCATIONS.items():
    out = SCRIPT_DIR / f'VODCA_CXKu_{name}.csv'
    if Path(out).exists():
        size_kb = Path(out).stat().st_size // 1024
        print(f"[{name}] skipping — {out} already exists ({size_kb} KB)")
        continue
    print(f"[{name}] building feature collection...")
    fc = ee.FeatureCollection(ckxu.map(make_extractor(aoi)))
    n = fc.size().getInfo()
    print(f"[{name}] {n} features — downloading to {out} ...")
    geemap.ee_to_csv(fc, filename=str(out))
    size_kb = Path(out).stat().st_size // 1024
    print(f"[{name}] done — {out} ({size_kb} KB)")