import streamlit as st
from streamlit_folium import folium_static
import folium
import geopandas as gpd

path = gpd.datasets.get_path('nybb')
df = gpd.read_file(path)
#print(df.head())

# Use WGS 84 (epsg:4326) as the geographic coordinate system
df = df.to_crs(epsg=4326)
print(df.crs)

# streamlit-folium"

with st.echo():
    import streamlit as st
    from streamlit_folium import folium_static
    import folium

    m = folium.Map(location=[40.70, -73.94], zoom_start=10, tiles='CartoDB positron')
    

    for _, r in df.iterrows():
    # Without simplifying the representation of each borough,
    # the map might not be displayed
        sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=0.001)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'orange'})
        folium.Popup(r['BoroName']).add_to(geo_j)
        geo_j.add_to(m)
    folium_static(m)   

# Project to WGS84 geographic crs

# geometry (active) column
    df = df.to_crs(epsg=2263)

# Access the centroid attribute of each polygon
    df['centroid'] = df.centroid
    df = df.to_crs(epsg=4326)
    # Centroid column
    df['centroid'] = df['centroid'].to_crs(epsg=4326)
    for _, r in df.iterrows():
        lat = r['centroid'].y
        lon = r['centroid'].x
        folium.Marker(location=[lat, lon],
                  popup='length: {} <br> area: {}'.format(r['Shape_Leng'], r['Shape_Area'])).add_to(m)
    folium_static(m)
    

# Centroid column
df['centroid'] = df['centroid'].to_crs(epsg=4326)

  
