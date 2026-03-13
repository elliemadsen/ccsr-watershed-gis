
// Have to import ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")

var box = ee.Geometry.BBox(-75.47, 42.04, -74.53, 42.48);

var sm_surface = imageCollection.select("sm_surface").filterBounds(box);

function plot(sm) {
  // print(sm.projection())
  var smSurfaceVis = {
    min: 0.0,
    max: 0.9,
    palette: ['0300ff', '418504', 'efff07', 'efff07', 'ff0303'],
  };
  Map.setCenter(-75, 42.2, 10);
  Map.addLayer(sm.clip(box), smSurfaceVis, 'SM Surface');
}

function exportMonth(month) {
  var projection = month.projection().getInfo();
  Export.image.toDrive({
    image: month,
    description: 'smap_sm_raw_9000m_monthly',
    region: box,
    scale: 9000,
    maxPixels: 1e13
  });
}

// var djf = sm_surface.filter(ee.Filter.calendarRange(12, 2, 'month'));
// var mam = sm_surface.filter(ee.Filter.calendarRange(3, 5, 'month'));
// var jja = sm_surface.filter(ee.Filter.calendarRange(6, 8, 'month'));
// var som = sm_surface.filter(ee.Filter.calendarRange(9, 11, 'month'));

var years = ee.List.sequence(2015, 2025);
var months = ee.List.sequence(1, 12);

var yearMonthMeans = ee.ImageCollection.fromImages(
  years.map(function(y) {
    return months.map(function(m) {
      
      var start = ee.Date.fromYMD(y, m, 1);
      var end   = start.advance(1, 'month');
      
      var monthlyCollection = sm_surface.filterDate(start, end);
      var image = ee.Image(
        ee.Algorithms.If(
          monthlyCollection.size().gt(0),
          monthlyCollection.filterBounds(box).mean()
            .set('year', y)
            .set('month', m)
            .set('system:time_start', start.millis()),
          null
        )
      );
      return image;
    });
  }).flatten()
);
yearMonthMeans = yearMonthMeans.filter(ee.Filter.notNull(['system:time_start']));
print(yearMonthMeans.size())

var projection = sm_surface.first().projection();
exportMonth(yearMonthMeans.toBands().reproject(projection).clip(box));
