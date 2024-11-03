# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd
import pickle
import geojson

#--------------------------------------------

# Variables
ss = st.session_state

# Callable

# Initialize
page_title = 'Find Routes'
page_icon = ':earth_asia:'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)

#---------------------------------------------

# Preparations

@st.cache_data(ttl = None, max_entries = 1)
def load_routes_data():
    folder = "discomfort_and_curve_data/routes_data/"

    with open(folder + 'sampled_nodes_for_curve_bike.pkl', 'rb') as f:
        b_list_nodes_sampled = pickle.load(f)

    with open(folder + 'sampled_nodes_for_curve_walk.pkl', 'rb') as f:
        w_list_nodes_sampled = pickle.load(f)

    bike_routes_dict = {}
    walk_routes_dict = {}

    for beta in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):

        beta = float(beta)

        filename_bike = folder + f"bike_lowest_objective_paths-beta_{beta}.pkl"
        filename_walk = folder + f"walk_lowest_objective_paths-beta_{beta}.pkl"

        with open(filename_bike, "rb") as f:
            b_path_dict = pickle.load(f)
        with open(filename_walk, "rb") as f:
            w_path_dict = pickle.load(f)

        bike_routes_dict[beta] = b_path_dict
        walk_routes_dict[beta] = w_path_dict

    return b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict

@st.cache_data(ttl = None, max_entries = 1)
def load_nodes_and_edges():
    folder = "discomfort_and_curve_data/"

    Gb_edges = gpd.read_feather(folder + "Gb_edges.feather")
    Gb_nodes = gpd.read_feather(folder + "Gb_nodes.feather")
    Gw_edges = gpd.read_feather(folder + "Gw_edges.feather")
    Gw_nodes = gpd.read_feather(folder + "Gw_nodes.feather")

    return Gb_edges, Gb_nodes, Gw_edges, Gw_nodes

@st.cache_data(ttl = None, max_entries = 1)
def load_brgy_geo():
    folder = "discomfort_and_curve_data/"

    brgy_geo_for_city = gpd.read_feather(folder + "brgy_geo_for_city.feather")

    return brgy_geo_for_city

# Main

if __name__ == "__main__":

    # SESSION STATE
    if any([x not in ss for x in ["b_list_nodes_sampled", "w_list_nodes_sampled", "bike_routes_dict", "walk_routes_dict"]]):
        b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict = load_routes_data()
        ss["b_list_nodes_sampled"] = b_list_nodes_sampled
        ss["w_list_nodes_sampled"] = w_list_nodes_sampled
        ss["bike_routes_dict"] = bike_routes_dict
        ss["walk_routes_dict"] = walk_routes_dict

    if any([key not in ss for key in ["Gb_edges", "Gb_nodes", "Gw_edges", "Gw_nodes"]]):
        Gb_edges, Gb_nodes, Gw_edges, Gw_nodes = load_nodes_and_edges()

        ss["Gb_edges"] = Gb_edges
        ss["Gb_nodes"] = Gb_nodes
        ss["Gw_edges"] = Gw_edges
        ss["Gw_nodes"] = Gw_nodes

    if "brgy_geo_for_city" not in ss:
        ss["brgy_geo_for_city"] = load_brgy_geo()

    # DATA
    b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict = ss["b_list_nodes_sampled"], ss["w_list_nodes_sampled"], ss["bike_routes_dict"], ss["walk_routes_dict"]

    Gb_edges, Gb_nodes, Gw_edges, Gw_nodes = ss["Gb_edges"], ss["Gb_nodes"], ss["Gw_edges"], ss["Gw_nodes"]

    brgy_geo_for_city = ss["brgy_geo_for_city"]


    # START
    st.markdown("# Find Routes based on Discomfort Sensitivity")

    mode_option = st.radio(
        "Mode of Active Transport",
        options = ["Cycling", "Walking"]
    )

    if mode_option == "Cycling":
        list_nodes_sampled = b_list_nodes_sampled
        routes_dict = bike_routes_dict
        edges = Gb_edges
        nodes = Gb_nodes

    elif mode_option == "Walking":
        list_nodes_sampled = w_list_nodes_sampled
        routes_dict = walk_routes_dict
        edges = Gw_edges
        nodes = Gw_nodes

    # Filter
    nodes = nodes.loc[list_nodes_sampled]

    # st.write(brgy_geo_for_city)

    # base1 = alt.Chart(brgy_geo_for_city).mark_geoshape(
    #     fill = "gray",
    #     stroke = "white"
    # ).project(
    #     "mercator" # epsg:4326 is spherical mercator
    # )

    # st.altair_chart(base1)

    import plotly.express as px

    df = brgy_geo_for_city

    fig = px.choropleth(df, geojson = df.geometry, locations = df.index, projection = "mercator")
    fig.update_geos(fitbounds="locations", visible=True)

    selection = st.plotly_chart(fig, selection_mode="points", on_select = "rerun")

    st.write(selection)


    df = nodes
    df["SIZE"] = 100

    fig = px.scatter_geo(df, geojson = df.geometry, projection = "mercator", size = "SIZE")
    # fig.update_geos(fitbounds="locations", visible=True)

    selection = st.plotly_chart(fig, selection_mode="points", on_select = "rerun")

    st.write(selection)

    # multi = alt.selection_point(on='click', nearest=True)

    # base = alt.Chart(pd.DataFrame(nodes.drop("geometry", axis = 1))).mark_point(
    #     filled = True
    # ).encode(
    #     x = "x",
    #     y = "y",
    #     color=alt.condition(multi, alt.value("red"), alt.value('gray'))
    # ).add_selection(multi)

    # chart = (
    #     base 
    # ).interactive()

    # selection_dict = st.altair_chart(
    #     chart,
    #     on_select = "rerun"
    # )

    # st.write(selection_dict)