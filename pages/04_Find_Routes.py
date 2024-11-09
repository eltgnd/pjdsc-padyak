# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd
import pickle


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


def load_routes_data():
    folder = "discomfort_and_curve_data/routes_data2/"

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

@st.cache_data(ttl = None, max_entries = 10)
def load_nodes_and_edges():
    folder = "discomfort_and_curve_data/"

    Gb_edges = gpd.read_feather(folder + "Gb_edges.feather")[["geometry"]].copy(deep = True)
    Gb_nodes = gpd.read_feather(folder + "Gb_nodes.feather")[["x", "y", "geometry"]].copy(deep = True).sort_values(["y", "x"], ascending = True)
    Gw_edges = gpd.read_feather(folder + "Gw_edges.feather")[["geometry"]].copy(deep = True)
    Gw_nodes = gpd.read_feather(folder + "Gw_nodes.feather")[["x", "y", "geometry"]].copy(deep = True).sort_values(["y", "x"], ascending = True)

    return Gb_nodes, Gw_nodes, Gb_edges, Gw_edges

@st.cache_data(ttl = None, max_entries = 10)
def load_brgy_geo():
    folder = "discomfort_and_curve_data/"
    brgy_geo_for_city = gpd.read_feather(folder + "brgy_geo_for_city.feather").fillna("")

    return brgy_geo_for_city

# Main

if __name__ == "__main__":

    # SESSION STATE
    if any([(key not in ss) for key in ["b_list_nodes_sampled", "w_list_nodes_sampled", "bike_routes_dict", "walk_routes_dict"]]):
        b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict = load_routes_data()
        ss["b_list_nodes_sampled"] = b_list_nodes_sampled
        ss["w_list_nodes_sampled"] = w_list_nodes_sampled
        ss["bike_routes_dict"] = bike_routes_dict
        ss["walk_routes_dict"] = walk_routes_dict

    if any([(key not in ss) for key in ["Gb_edges", "Gb_nodes", "Gw_edges", "Gw_nodes"]]):
        (Gb_nodes, Gw_nodes,
         Gb_edges, Gw_edges
        ) = load_nodes_and_edges()

        ss["Gb_edges"] = Gb_edges
        ss["Gb_nodes"] = Gb_nodes
        ss["Gw_edges"] = Gw_edges
        ss["Gw_nodes"] = Gw_nodes

    if "brgy_geo_for_city" not in ss:
        ss["brgy_geo_for_city"] = load_brgy_geo()

    # DATA
    b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict = ss["b_list_nodes_sampled"], ss["w_list_nodes_sampled"], ss["bike_routes_dict"], ss["walk_routes_dict"]

    Gb_edges, Gw_edges = ss["Gb_edges"], ss["Gw_edges"]
    Gb_nodes, Gw_nodes = ss["Gb_nodes"], ss["Gw_nodes"]

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
    nodes_selectable = nodes.loc[list_nodes_sampled]

    # widgets

    node_o = st.selectbox(
        "Origin",
        options = nodes_selectable.index,
        index = 0,
        format_func = lambda x: f"Node {x}"
    )

    node_d = st.selectbox(
        "Destination",
        options = nodes_selectable.index,
        index = 10,
        format_func = lambda x: f"Node {x}"
    )

    if node_o == node_d:
        st.warning("Choose two different nodes.")
        st.stop()

    # Determine path based on beta

    beta = st.select_slider(
        "Beta (Sensitivity to Discomfort)",
        options = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        value = 0.0
    )

    path_nodes = routes_dict[beta][f"{node_o}, {node_d}"]
    pairs = set([(path_nodes[i], path_nodes[i+1]) for i in range(0, len(path_nodes) - 1)])

    edge_index_frame = edges.index.to_frame()
    edge_mask = edge_index_frame[["u", "v"]].apply(lambda r: (r['u'], r['v']), axis = 1).isin(pairs)

    # Graph

    fig, ax = plt.subplots(figsize = (10, 8))
    ax.set_xlim(0.015+1.21e2, 0.065+1.21e2)
    ax.set_ylim(14.565, 14.602)
    plt.axis(False)

    # city
    brgy_geo_for_city.plot(aspect = 1, ax = ax, color = "black")

    # plot the edges
    edges.plot(
        aspect = 1,
        ax = ax,
        color = "white"
    )

    edges.loc[edge_mask].plot(
        aspect = 1,
        ax = ax,
        color = "yellow",
        linewidth = 5,
    )

    # plot the nodes
    nodes_selectable.loc[[node_o, node_d]].plot(
        ax = ax,
        color = "red",
        markersize = 500,
    )

    ### this can be used to verify that the filtered edges actually reflect the path as described in the list
    # nodes.loc[path_nodes].plot(
    #     ax = ax,
    #     color = "blue",
    #     markersize = 100,
    # )

    st.pyplot(fig, use_container_width=True, clear_figure=False)