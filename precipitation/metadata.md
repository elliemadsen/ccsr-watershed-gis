ACCESS-ESM1-5 (hot/wet)

IPSL-CM6A-LR (hot/dry)

Currently the data is from 2015-2065, for SSP3-7.0.

Each .csv file is named Catskills*[MODEL]*[variable]\_[scenario]\_daily_avg.csv and has a column for each of the 6 grid cells named with the latitude and longitude of the center of the grid cell. There should be a row for each date.

The variables/units are described in the tech note (page 3): https://www.nccs.nasa.gov/sites/default/files/NEX-GDDP-CMIP6-v2-Tech_Note.pdf

Task:
Create some 3D visualizations of the Cannonsville visualizing different time series data over the reservoir basin, starting with precip changes over time.
View the precip data as a recurring GIF over the reservoir basin (at whatever time step is best, starting from 2015). Would be neat to see them side by side.

Notes:

- I will use three.js (if feasible) to view the 3d DEM in browser.
- There are six reservoir basins. The precipitation data in each file has one column per basin centroid (lat/lon).
- I will need to map each centroid lat/lon (csv column) to its geometry in a separate geojson (or other file format if easier).
- The data is daily. I will aggregate by month. Start with mean for the aggregation, and in the future we could add min/max, etc. This should probably be done preprosseced to create versions of the file like Catskills*[MODEL]*[variable]\_[scenario]\_monthly_avg.csv
- There will be a slider in the window for time. The user will drag it to change the current month, from 2015 to 2065.
- There will also be a dropdown for the dataset: ([MODEL]\*[variable]\_[scenario]).
- The DEM will be colored by each basin's precipitation value at the current time.
- After this works, I'll add functionality to export GIFs.
