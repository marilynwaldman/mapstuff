from geopandas.geodataframe import GeoDataFrame
import pandas as pd
import numpy as np
import geopandas as gpd
import streamlit as st
import folium as fl
import streamlit_folium as sf
import branca.colormap as cm
import os as os
import pathlib
import zipfile
import requests

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

    save_response_content(response, destination)    

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


def main():
    waterdistrict_gdf = get_districtsgdf()
    st.write(waterdistrict_gdf.head())
if __name__ == "__main__":
    main()