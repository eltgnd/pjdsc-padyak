# Packages
import streamlit as st
import pandas as pd
import geopandas as gpd
import leafmap.foliumap as leafmap
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import seaborn as sns
import folium
from functools import partial

# Variables
ss = st.session_state
default_index_column = 'score_weighted_by_sub'
default_weight = 5
default_feature_cmap = plt.get_cmap('PuOr_r')
geofabrik_cleaned_options = [ 
    'sidewalk_description',
    'has_left_sidewalk_status',
    'has_right_sidewalk_status',
    'is_crossing_status',
    'bicycle_status',
    'parking_left_description',
    'parking_right_description',
    'cycleway_class',
    'cycleway_description',
    'cycleway_lane_type',
    'cycleway_left_class',
    'cycleway_left_lane_type',  
    'cycleway_right_class',
    'cycleway_right_lane_type',]

# Helper functions
@st.cache_data
def import_data():
    bike = gpd.read_file(f"{folder_location}/streamlit_final_bike.geojson")
    walk = gpd.read_file(f"{folder_location}/streamlit_final_walk.geojson")
    return bike,walk

# Function to apply color transformation using partial instead of lambda
def color_mapping(value, cmap, norm):
    return colors.rgb2hex(cmap(norm(value)))

def compute_colors(gdf, default_index_column, cmap, norm):
    gdf = gdf.copy()
    color_func = partial(color_mapping, cmap=cmap, norm=norm)
    gdf["color"] = gdf[default_index_column].apply(color_func)
    return gdf

# Define the style function separately to avoid lambda issues with caching
def style_function(feature):
    return {
        'color': feature['properties']['color'],
        'weight': 5
    }

# Define tooltip fields and aliases function for GeoJsonTooltip
def tooltip_function(index_name):
    return folium.GeoJsonTooltip(fields=['osmid', 'index_value'], aliases=['OSMID', index_name])

def get_index_layer(gdf, index_name, default_index_column=default_index_column, end_color_saturation=100):
    columns = ['geometry', default_index_column, 'osmid']
    gdf = gdf[columns]
    gdf = gdf.rename(columns={default_index_column: 'index_value'})

    # Setup color mapping only once
    vmin, vmax = gdf['index_value'].min(), gdf['index_value'].max()
    vcenter = gdf['index_value'].median()
    norm = colors.TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    cmap = sns.diverging_palette(10, 145, center="light", s=end_color_saturation, as_cmap=True)

    # Apply precomputed color mapping
    gdf = compute_colors(gdf, 'index_value', cmap, norm)
    gdf['index_value'] = gdf['index_value'].round(2) # Format to presentable numbers

    # Simplify by using a GeoJSON layer instead of individual Polylines
    feature_group = folium.FeatureGroup(name=index_name)
    folium.GeoJson(
        data=gdf.to_json(),
        style_function=style_function,
        tooltip=tooltip_function(index_name)
    ).add_to(feature_group)
    
    return feature_group

def format_geo(s):
    return s.replace('_', ' ').title()

def format_component(s):
    return s[3:].replace('_', ' ').title()

def get_feature_color(val, mn, mx):
    norm_x = (val-mn)/(mx-mn)
    clr = default_feature_cmap(norm_x)
    return colors.rgb2hex(clr)


# Initialize
page_title = 'Padyak'
page_icon = '🚶‍♂️‍➡️'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide", initial_sidebar_state="auto", menu_items=None)

st.image('https://i.imgur.com/965KImX.png',width=75)
st.title('PADYAK: Walkability and Bikeability Index Modeling for Sustainable Mobility Planning')


# Load map data
folder_location = 'streamlit_preparation'
with st.status('Loading data...'):
    bike, walk = import_data()
    ss['bike'] = bike
    ss['walk'] = walk

# Generate map
m = leafmap.Map(center=(14.581138, 121.041542), zoom=14, draw_control=False, google_map="TERRAIN")

@st.cache_data
def add_index_layers():
    bike_layer = get_index_layer(bike, 'Bikeability')
    walk_layer = get_index_layer(walk, 'Walkability')
    return bike_layer, walk_layer

# Add layers to map
with st.spinner('Adding data to map...'):
    bike_layer, walk_layer = add_index_layers()
    bike_layer.add_to(m)
    walk_layer.add_to(m)

st.write('\n')

# Define a form for selecting street features for hover display
with st.form("street_infrastructure_form"):
    st.caption('STREET INFRASTRUCTURE ATTRIBUTES')
    
    geofabrik_formatted = [format_geo(x) for x in geofabrik_cleaned_options]
    selected = st.multiselect("Select street features to display on hover", geofabrik_formatted)
    update_street_features = st.form_submit_button("Update Street Features")
    if update_street_features and selected:
        selected_categorical = [geofabrik_cleaned_options[geofabrik_formatted.index(x)] for x in selected]
        m.add_gdf(bike[['geometry'] + selected_categorical], layer_name='Street Features')

# Define a separate form for component visualization and map layer updates
with st.form("component_visualization_form"):
    st.caption('COMPONENT VISUALIZATION')
    
    option = st.radio("Select dataset", ['Bikeability', 'Walkability'], horizontal=True)
    
    if option:
        gdf = bike if option == 'Bikeability' else walk
        main_components = [x for x in gdf.columns.tolist() if x[:3] == 'MU_']
        main_components_formatted = [format_component(x) for x in main_components]
        
        selected_numerical = st.multiselect("Select components to display as colored layers", main_components_formatted)
        
        update_map_layers = st.form_submit_button("Update Map Layers")
        if update_map_layers:
            for i in selected_numerical:
                feature = main_components[main_components_formatted.index(i)]
                min_val, max_val = gdf[feature].min(), gdf[feature].max()
                style_function = lambda x: {
                    'color': get_feature_color(x['properties'][feature], min_val, max_val),
                    'weight': default_weight
                }
                m.add_gdf(gdf[['geometry', feature]].round(2), layer_name=f"{option}: {i}", style_function=style_function)


# Display map
with st.container(border=True):
    m.to_streamlit()
