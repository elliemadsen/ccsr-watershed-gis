
// Have to import ee.ImageCollection("LANDSAT/COMPOSITES/C02/T1_L2_8DAY_NDVI")

var box = ee.Geometry.BBox(-75.47, 42.04, -74.53, 42.48);

var ndvi = imageCollection
  .select('NDVI')
  .filterBounds(box);

var years = ee.List.sequence(2015, 2025);
var months = ee.List.sequence(1, 12);

var yearMonthMeans = ee.ImageCollection.fromImages(
  years.map(function(y) {
    return months.map(function(m) {

      var start = ee.Date.fromYMD(y, m, 1);
      var end = start.advance(1, 'month');

      var monthly = ndvi.filterDate(start, end);

      var img = ee.Image(
        ee.Algorithms.If(
          monthly.size().gt(0),
          monthly.mean()
            .rename(
              ee.String('NDVI_')
                .cat(ee.Number(y).format('%04d'))
                .cat('_')
                .cat(ee.Number(m).format('%02d'))
            )
            .set('system:time_start', start.millis()),
          null
        )
      );

      return img;
    });
  }).flatten()
);

// Remove null months
yearMonthMeans = yearMonthMeans.filter(
  ee.Filter.notNull(['system:time_start'])
);

print('Months:', yearMonthMeans.size());

// Convert to bands
var monthlyBands = yearMonthMeans.toBands().clip(box);

// Export
Export.image.toDrive({
  image: monthlyBands,
  description: 'NDVI_monthly_2015_2025',
  region: box,
  scale: 30,
  maxPixels: 1e13
});
