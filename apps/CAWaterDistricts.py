
from geopandas.geodataframe import GeoDataFrame
import pandas as pd
import numpy as np
import geopandas as gpd
import streamlit as st
import folium as fl
from folium.plugins import FastMarkerCluster,MarkerCluster,MiniMap
import streamlit_folium as sf
import streamlit.components.v1 as components
import branca.colormap as cm
import os as os
import pathlib
import zipfile
import requests
from streamlit_folium import folium_static
import time

STREAMLIT_STATIC_PATH = pathlib.Path(st.__path__[0]) / "static"
print(STREAMLIT_STATIC_PATH)
# We create a downloads directory within the streamlit static asset directory
# and we write output files to it
DOWNLOADS_PATH = STREAMLIT_STATIC_PATH / "downloads"
if not DOWNLOADS_PATH.is_dir():
    DOWNLOADS_PATH.mkdir() 

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response,destination)  


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


def get_districtsgdf():

    out_zip = os.path.join(DOWNLOADS_PATH, "Water_Districts.zip")
    file_id = '1Ng9v8HQrTRd8BQUgIZFgbG2Ht0tCfcM2'
    download_file_from_google_drive(file_id, out_zip)
    zip_ref = zipfile.ZipFile(out_zip, "r")
    zip_ref.extractall(DOWNLOADS_PATH)

    gdf = gpd.read_file(out_zip.replace("zip", "shp"))

    return gdf  

def get_countiesgdf(allow_output_mutation=True):

    out_zip = os.path.join(DOWNLOADS_PATH, "CaliforniaCounties.zip")
    #https://drive.google.com/file/d/1-J2JhrRHazBfbM7M_pwPB5D2XWGIthHJ/view?usp=sharing
    file_id = '1-J2JhrRHazBfbM7M_pwPB5D2XWGIthHJ'
    download_file_from_google_drive(file_id, out_zip)
    zip_ref = zipfile.ZipFile(out_zip, "r")
    zip_ref.extractall(DOWNLOADS_PATH)
    gdf = gpd.read_file(out_zip.replace("zip", "shp"))

    return gdf                          
@st.cache(allow_output_mutation=True)
def get_county_dict():
    # returns a dictonary of lists of California regions: Southern, Northern and Midsecton

    SoCalCountyList = ['Imperial', 'Inyo',  
                   'Los Angeles', 'Mono', 'Orange', 
                   'Riverside', 'San Bernardino', 'San Diego', 
                   'San Luis Obispo', 'Santa Barbara', 'Ventura']
    AdjNoCalCountyList = ['Monterey', "Fresno", 'Kings', "San Benito",
                      "Tulare"]
    MidCalCounties = ['Monterey', "Fresno", 'Kings', "San Benito",
                     "Tulare", 'Inyo',  'Kern', 'San Bernardino',
                      'Los Angeles', 'San Luis Obispo',
                      'Santa Barbara', 'Ventura']                  

    MidSectionCACountyList = SoCalCountyList + AdjNoCalCountyList

    NorthCalCountyList = ['Kern','Kings','Lake','Lassen','Madera','Marin',
                  'Mariposa','Mendocino','Merced', 'Modoc','Monterey', 'Napa', 'Nevada',
                  'Placer','Plumas', 'Sacramento', 'San Benito', 'San Francisco',
                  'San Joaquin','San Mateo', 'Santa Clara', 'Santa Cruz', 'Shasta',
                  'Sierra', 'Siskiyou', 'Solano', 'Alameda', 'Alpine', 'Sonoma', 'Amador',
                  'Stanislaus','Sutter', 'Butte', 'Calaveras', 'Tehama', 'Colusa',
                  'Trinity', 'Tulare', 'Contra Costa', 'Del Norte', 'Tuolumne', 'El Dorado',
                  'Fresno', 'Glenn', 'Yuba','Yolo','Humboldt']

    CentralCalCountyList = ["Butte", "Colusa", "Glenn", "Fresno", "Kern", "Kings", 
                            "Madera", "Merced", "Placer", 
                            "San Joaquin", "Sacramento", "Shasta", "Solano", "Stanislaus", 
                            "Sutter", "Tehama", "Tulare", "Yolo", "Yuba"]


    ca_county_dict = {
         "Southern California" : SoCalCountyList,
         "Northern California" : NorthCalCountyList,
         "California Mid-Section" : MidSectionCACountyList,
         "Central California" : CentralCalCountyList,
         "Mid-California Counties" : MidCalCounties
    }
    
    return ca_county_dict

def get_counties(gdf, cnty_list):
    boolean_series = gdf.NAME.isin(cnty_list)
    cnty_gdf = gdf[boolean_series].reset_index(drop=True)
    return cnty_gdf
    
    
def get_water_districts(waterdistict_gdf, county_selections_gdf):
    waterdistict_gdf_utm10 = waterdistict_gdf.to_crs( "epsg:26910")
    county_selections_gdf_utm10 = county_selections_gdf.to_crs( "epsg:26910")
    wd_in_selected_counties = waterdistict_gdf_utm10.intersects(county_selections_gdf_utm10.geometry.unary_union)
    #waterdistict_gdf_utm10[wd_in_selected_counties]
    
    return  waterdistict_gdf_utm10[wd_in_selected_counties] 

       
def get_random(gdf, n):
    
    np.random.seed(42)
    #gdf['Color'] = random.uniform(0, 1) * gdf.shape[0]
    gdf['Color'] = np.random.randint(1, n, gdf.shape[0]).astype(float)
    #print(gdf['Color'].head())
    return gdf

def add_counties(calmap,gdf):
    
    fl.GeoJson(gdf, name='California Counties', control=True,
               style_function = lambda x: {"weight":0.5, 
                            'color':'grey',
                            'fillColor':'transparent',
#                            'fillColor':colormap_county(x['properties']['Active']), 
                            'fillOpacity':0.5
               },
               highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.75, 
                                'weight': 0.1
               },
               
               tooltip=fl.GeoJsonTooltip(
                   fields=['NAME'],
                   aliases=['County:'],
                   labels=True,
                   localize=True
               ),
               
           
              ).add_to(calmap)
    return calmap


def add_districts(calmap, gdf):

    gdf.to_crs('EPSG:4269')
    
    # create random index value for color map
    color_gdf = get_random(gdf, 10)
    color_gdf = color_gdf.set_index("GlobalID")
    color_dict = color_gdf["Color"]
    linear = cm.linear.YlGnBu_09.scale(0, 12)
    #Style and draw map
    fl.GeoJson(color_gdf, name='Water Districts', control=True,
           
              style_function = lambda x: {"weight":1.5, 
                                       'color':'grey',
#                                       'fillColor':'transparent',
                            'fillColor': linear(color_dict[x["id"]]), 
                            'fillOpacity':0.25
               },
           
               highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.5, 
                                'weight': 0.1
               },
               
               
               tooltip=fl.GeoJsonTooltip(
                   fields=['AGENCYNAME',],
                   aliases=['AGENCYNAME'],
                   labels=True,
                   localize=True
               ),
               
               
               ).add_to(calmap)
    
    return calmap

# Read data and cleans - pit data
def get_pits_df():
    
    df = pd.read_csv('../data/CA_WastewaterPits_Fractracker/pits.csv')
    
    return df

#aggregate pit df and return a list of top n Operators
def get_pits_top_n(df, n):
    
    pit_hist = df.groupby('Operator').sum().sort_values(by='Sites',ascending=False)
    pitlist = pit_hist['Sites'].index.values.tolist()
    
    return pitlist[0:n]

# getgdf (df, col_name, col_value)
# helper function

def getgdf(df, column_name, column_value):
    # input a dataframe, a column and column value
    # returns -  geopandas dataframe with lat/lon
    odf  =  df[df[column_name] == column_value]
    odfgpd = gpd.GeoDataFrame(odf,geometry=gpd.points_from_xy(odf.Longitude, odf.Latitude))
    return(odfgpd)

def get_pit_markers(mlist, df, calmap, zoom_max):
    
    for operator in mlist:
        gdfpit = getgdf(df, "Operator", operator)
        gdfpit.set_crs('EPSG:4269',inplace=True)
        marker_name = operator 
        opmarker = MarkerCluster(name=marker_name,overlay=True,control=True,disableClusteringAtZoom=zoom_max,
                              spiderfyOnMaxZoom=zoom_max)

        # Note that CircleMarkers are saved to the MarkerCluster layer, not the map
        gdfpit.apply(lambda row:
                        fl.CircleMarker(name='Pit Markers', control=True, zindexoffset=1000,
                                  location=[row['geometry'].y, row['geometry'].x],
                                  radius=5,
                                  color='orange',
                                  fill=True,
                                  fill_color='yellow',
                                  popup=row['Operator'],
                            
               highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.25, 
                                'weight': 0.1
               },
               
               tooltip = "Operator: %s<br>Pits: %s" % (row['Operator'], row['Sites'])             

                                 ).add_to(opmarker), 
                         axis=1)


               
        #Add the Markeluster layer to the map
        opmarker.add_to(calmap)
        
    return(calmap)
              

def main():
    
    
            
    
    waterdistrict_gdf = get_districtsgdf()
    ca_counties_gdf = get_countiesgdf()
    df_pits = get_pits_df()
    county_dict = get_county_dict()
    selection = "Mid-California Counties"
    county_selections_gdf = get_counties(ca_counties_gdf, county_dict[selection])
    water_dist_selection_gdf = get_water_districts(waterdistrict_gdf, county_selections_gdf)
    pit_list = get_pits_top_n(df_pits, 3)

    CAwaterDistrictMap = fl.Map(title = "California Pits",location=[35.37,-119.02],
                zoom_start=6,tiles=None)
    fl.TileLayer('cartodbpositron',name='BackGround',control=False).add_to(CAwaterDistrictMap)
    

    CAwaterDistrictMap = add_counties(CAwaterDistrictMap,ca_counties_gdf)
    CAwaterDistrictMap = add_districts(CAwaterDistrictMap,water_dist_selection_gdf)
    CAwaterDistrictMap = get_pit_markers(pit_list, df_pits, CAwaterDistrictMap, zoom_max = 15)
    fl.LayerControl(collapsed=True).add_to(CAwaterDistrictMap)
    st.title("California Pits and Ponds")
    folium_static(CAwaterDistrictMap) 
    CAwaterDistrictMap.save("CenCal2.html")

    

if __name__ == "__main__":
    main()