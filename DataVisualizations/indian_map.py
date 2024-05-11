# Visualizing data on the map of India
"""
    Also contains data sources and notes on the Indian map.
"""

# %%[markdown]
"""
# Data Download

There are two sources (as mentioned below)

## Surveys of India

Official maps from Survey of India (Ministry of Science and 
Technology, Government of India):
https://onlinemaps.surveyofindia.gov.in/Digital_Product_Show.aspx <br>
This requires creating an account and downloading the maps as 
ShapeFiles.

## GDAM (from UC Davis)

Download the map from here: https://gadm.org/download_country.html

```bash
# Shapefiles (with multiple levels)
wget https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_IND_shp.zip
# Geopackage
wget https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_IND.gpkg
# GeoJSON
wget https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_0.json
wget https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_1.json.zip
wget https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_2.json.zip
wget https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_3.json.zip
```
"""

# %%[markdown]
"""
# Notes

## Coordinate Systems

The default data is in Geographic Coordinate System (GCS) of
EPSG:4326. We need to convert it to a Coordinate Reference System
(CRS) of EPSG:7755 (that suits Indian subcontinent). GCS is a global
system (lat/long) and CRS is a local system (x/y). Another common CRS
for India is EPSG:24383.

- https://epsg.io/4326
- https://epsg.io/7755
- https://epsg.io/24383

> ESPG stands for European Petroleum Survey Group (though it has a
broader scope in GIS now). 

There are also websites for custom projection (for GIS software)

- https://projectionwizard.org/

## Data from GADM (UC Davis Geodata)

### For IND_0 or the GeoData (.gpkg) file

1. This is NOT the official map of India. Use the maps from Survey
    of India (MST, GoI) for the official map.
2. It shows India into multiple parts (classified under the "GID_0" 
    column): 
    - IND: Mainland India 
    - Z01: The entire India administered Jammu and Kashmir and the
        disputed territories of J&K in the western sector (with
        Pakistan on the west and China on the east).
    - Z04: Some disputed areas of the central sector. In Himachal 
        Pradesh; east of Tabo and the Dhar Kawe ranges.
    - Z05: Some disputed areas of the central sector. In 
        Uttarakhand; east of Barmatia ranges.
    - Z07: The entire state of Arunachal Pradesh in the eastern 
        sector.
    - Z09: Disputed areas in the central sector. In Uttarakhand;
        north of Gangotri ranges and the Pulma Sumda region.
3. Know more about disputed territories: https://knowledgekart.in/blog/disputed-territories-of-india-upsc-2020-international-relations/

### For IND_1 file

1. It contains "state-level" data for all of India (including all
    the territories mentioned above as a part of India).
2. The state or UT name is in "NAME_1" column.
3. The type ("State" or "Union Territory") is in the "ENGTYPE_1" 
    column. 
4. Some extra notes
    
    - "Delhi" is represented as "NCT of Delhi"
    - Himachal Pradesh is misclassified as a UT (it's actually a 
        State)
    - "Dadra and Nagar Haveli and Daman and Diu" is misclassified 
        as separate UTs (they're actually single): "Daman and Diu" and
        "Dadra and Nagar Haveli" (they're one since 2020). Also, a
        part of Dadra is shown in Gujarat and an enclave of Gujarat is
        missing.
    - "Ladakh" is incorrectly shown as a part of "Jammu and 
        Kashmir"
    
5. It contains the GID_0 from "IND_0" file notes above. It also
    contains "GID_1" colum which is a sub-classifier/ID.

### For IND_2 file

1. It contains the "district-level" data for all of India (similar 
    to IND_1 above). - The district name is in "NAME_2" column. The 
    state name is in the "NAME_1" column.
2. There is a hierarchical code in the "HASC_2" column.

### For IND_3 file

1. It contains the "taluk" level data. However, not all taluks are
    properly defined.
2. The taluk name is in "NAME_3" column. Sometimes it could be 
    "n.a." values.

## Data from MST (Government of India)

1. Some state and place names have symbols like: ">" instead of
    "a", "|" instead of "i", etc.

## Shapefile extensions

All these files are read when loading the ".shp" file; and are for
different purposes

1. ".shp" is the ShapeFile storing the actual geometric shape
2. ".shx" is for indexing the shape file (for faster access)
3. ".dbf" is for storing the attributes of the geometric shape
4.   (like name, type of region, etc.)
5. ".prj" is the geometric projection for the coordinate system
6. ".cpg" contains encoding information (mainly for the ".dbf" 
7.   file)
8. ".shp.xml" stores the metadata for the ShapeFile
9. ".sbn" is a binary representation of the shape file (mostly
    proprietary)
10. ".sbx" is to index things in the ".sbn" file (mostly 
    proprietary)

### Other File Extensions

- ".gpkg" is the GeoPackage file (contains everything in one file)
"""

# %%
import folium
m = folium.Map(location=[12.8830709, 77.5986285], zoom_start=17)
m

# %%
import geopandas as gpd
from pyproj import CRS


# %%
def show_india_data(filename: str, shift_crs:bool = True):
    data = gpd.read_file(filename)
    if shift_crs:
        data = data.to_crs(epsg=7755)   # Convert 4326 to 7755
    data["area_km_2"] = data.area / 1e6
    return data


# %%[markdown]
"""
# GDAM Maps (UC Davis)
"""

# %%
data = show_india_data("./gadm41_IND.gpkg") # India geopackage
data.explore("area_km_2", legend=False)

# %%
data = show_india_data("./shapefiles/gadm41_IND_0.shp") # Country
data.explore("area_km_2", legend=False)

# %%
data = show_india_data("./shapefiles/gadm41_IND_1.shp") # States
data.explore("area_km_2", legend=False)

# %%
data = show_india_data("./shapefiles/gadm41_IND_2.shp") # Districts
data.explore("area_km_2", legend=False)

# %%
data = show_india_data("./shapefiles/gadm41_IND_3.shp") # Taluks
data.explore("area_km_2", legend=False)

# %%[markdown]
"""
# Survey of India Maps
"""

# %%
data = show_india_data("./soi/STATE_BOUNDARY.shp", False)  # States
data.explore("area_km_2", legend=False)

# %%
data = show_india_data("./soi/DISTRICT_BOUNDARY.shp", 
        False)  # Districts
data.explore("area_km_2", legend=False)

# %%
