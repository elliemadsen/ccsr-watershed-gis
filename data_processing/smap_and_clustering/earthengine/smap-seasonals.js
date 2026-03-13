
// Have to import ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")

var box = ee.Geometry.BBox(-75.47, 42.04, -74.53, 42.48);

function seasonForYear(year, season) {

  year = ee.Number(year);
  season = ee.String(season);

  var start = ee.Algorithms.If(
    season.equals('DJF'),
    ee.Date.fromYMD(year.subtract(1), 12, 1),
    ee.Algorithms.If(
      season.equals('MAM'),
      ee.Date.fromYMD(year, 3, 1),
      ee.Algorithms.If(
        season.equals('JJA'),
        ee.Date.fromYMD(year, 6, 1),
        ee.Date.fromYMD(year, 9, 1)
      )
    )
  );

  var end = ee.Algorithms.If(
    season.equals('DJF'),
    ee.Date.fromYMD(year, 3, 1),
    ee.Algorithms.If(
      season.equals('MAM'),
      ee.Date.fromYMD(year, 6, 1),
      ee.Algorithms.If(
        season.equals('JJA'),
        ee.Date.fromYMD(year, 9, 1),
        ee.Date.fromYMD(year, 12, 1)
      )
    )
  );

  return imageCollection.select("sm_surface").filterDate(start, end).mean();
}

function seasonalClimatology(season, startYear, endYear) {

  var years = ee.List.sequence(startYear, endYear);

  var seasonalImages = years.map(function(y) {
    return seasonForYear(y, season);
  });

  return ee.ImageCollection.fromImages(seasonalImages)
    .mean()
    .set('season', season)
    .set('startYear', startYear)
    .set('endYear', endYear);
}

var startYear = 2015;
var endYear   = 2025;

var DJF = seasonalClimatology('DJF', startYear+1, endYear);
var MAM = seasonalClimatology('MAM', startYear, endYear);
var JJA = seasonalClimatology('JJA', startYear, endYear);
var SON = seasonalClimatology('SON', startYear, endYear);

Export.image.toDrive({
  image: DJF,
  description: 'SMAP_DJF',
  region: box,
  scale: 9000,
  maxPixels: 1e13
});
// Export.image.toDrive({
//   image: MAM,
//   description: 'SMAP_MAM',
//   region: box,
//   scale: 9000,
//   maxPixels: 1e13
// });
// Export.image.toDrive({
//   image: JJA,
//   description: 'SMAP_JJA',
//   region: box,
//   scale: 9000,
//   maxPixels: 1e13
// });
// Export.image.toDrive({
//   image: SON,
//   description: 'SMAP_SON',
//   region: box,
//   scale: 9000,
//   maxPixels: 1e13
// });
