# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd
import pickle
import leafmap.foliumap as leafmap
import folium
from streamlit_folium import st_folium


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

    Gb_edges = gpd.read_feather(folder + "Gb_edges.feather")[["geometry"]].copy(deep = True).select_dtypes(exclude=['datetime']).set_crs("EPSG:4326")
    Gb_nodes = gpd.read_feather(folder + "Gb_nodes.feather")[["x", "y", "geometry"]].copy(deep = True).sort_values(["y", "x"], ascending = True).select_dtypes(exclude=['datetime']).set_crs("EPSG:4326")
    Gw_edges = gpd.read_feather(folder + "Gw_edges.feather")[["geometry"]].copy(deep = True).select_dtypes(exclude=['datetime']).set_crs("EPSG:4326")
    Gw_nodes = gpd.read_feather(folder + "Gw_nodes.feather")[["x", "y", "geometry"]].copy(deep = True).sort_values(["y", "x"], ascending = True).select_dtypes(exclude=['datetime']).set_crs("EPSG:4326")

    return Gb_nodes, Gw_nodes, Gb_edges, Gw_edges

@st.cache_data(ttl = None, max_entries = 10)
def load_brgy_geo():
    folder = "discomfort_and_curve_data/"
    brgy_geo_for_city = gpd.read_feather(folder + "brgy_geo_for_city.feather").fillna("").select_dtypes(exclude=['datetime']).set_crs("EPSG:4326")
    city_geo = gpd.GeoDataFrame({"geometry": [brgy_geo_for_city.union_all()]})

    return brgy_geo_for_city, city_geo

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

    if any([(key not in ss) for key in ["brgy_geo_for_city", "city_geo"]]):
        a, b = load_brgy_geo()
        ss["brgy_geo_for_city"] = a
        ss["city_geo"] = b

    # DATA
    b_list_nodes_sampled, w_list_nodes_sampled, bike_routes_dict, walk_routes_dict = ss["b_list_nodes_sampled"], ss["w_list_nodes_sampled"], ss["bike_routes_dict"], ss["walk_routes_dict"]

    Gb_edges, Gw_edges = ss["Gb_edges"], ss["Gw_edges"]
    Gb_nodes, Gw_nodes = ss["Gb_nodes"], ss["Gw_nodes"]

    brgy_geo_for_city = ss["brgy_geo_for_city"]
    city_geo = ss["city_geo"]


    # START
    st.markdown("# Find Routes based on Discomfort Sensitivity")

    mode_option = st.radio(
        "Mode of Active Transport",
        options = ["Cycling", "Walking"],
        horizontal=True
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

    # Filter to selectable nodes (nodes that had been sampled from the complete set of nodes)
    nodes_selectable = nodes.loc[list_nodes_sampled]

    # Choose origin and destination via node ID

    method_options = ["Node ID (input identifier of a location)", "Map (click to select points)"]

    method_of_node_selection = st.radio(
        "Select origin and destination by:",
        options = (0, 1),
        format_func = lambda x: method_options[x]
    )

    st.divider()

    if method_of_node_selection == 0:

        col1, col2 = st.columns([1, 1])

        with col1:

            node_o = st.selectbox(
                "Origin",
                options = nodes_selectable.index,
                index = 0,
                format_func = lambda x: f"Node {x}"
            )

        with col2:

            node_d = st.selectbox(
                "Destination",
                options = nodes_selectable.index,
                index = 10,
                format_func = lambda x: f"Node {x}"
            )

        if node_o == node_d:
            st.warning("Choose two different points as origin and destination.")
            st.stop()

    elif method_of_node_selection == 1:
    
        # Map for selecting nodes

        if "rerun_just_occurred" not in ss:
            ss["rerun_just_occurred"] = False

        if "SELECT_ORIGIN_node_was_manually_changed" not in ss:
            ss["SELECT_ORIGIN_node_was_manually_changed"] = False
        if "SELECT_DESTINATION_node_was_manually_changed" not in ss:
            ss["SELECT_DESTINATION_node_was_manually_changed"] = False


        # for origin
        key_prefix = "SELECT_ORIGIN"

        pt_previous_key = f"{key_prefix}_pt_previous"
        nearest_node_key = f"{key_prefix}_nearest_node"
        node_was_manually_changed_key = f"{key_prefix}_node_was_manually_changed"

        if pt_previous_key not in ss:
            ss[pt_previous_key] = None

        if (nearest_node_key not in ss) or (node_was_manually_changed_key not in ss):
            default_osmid = 1467807116
            ss[nearest_node_key] = {
                "Node ID": default_osmid,
                "Latitude": nodes_selectable.at[default_osmid, "y"],
                "Longitude": nodes_selectable.at[default_osmid, "x"]
            }
            ss[node_was_manually_changed_key] = True

        @st.fragment
        def select_node_ORIGIN():

            key_prefix = "SELECT_ORIGIN"

            pt_previous_key = f"{key_prefix}_pt_previous"
            nearest_node_key = f"{key_prefix}_nearest_node"
            node_was_manually_changed_key = f"{key_prefix}_node_was_manually_changed"

            mapcenter = (14.581912, 121.037947)

            m1 = leafmap.Map(center = mapcenter)

            m1.add_gdf(
                city_geo,
                layer_name = "Mandaluyong",
                style_function = lambda x: {
                    "color": "black",
                    "opacity": 0.5,
                    "fillOpacity": 0.0,
                    "fillColor": "none",
                },
                control = False # this disables toggle
            )

            if ss[nearest_node_key] is not None:

                m1.add_marker(
                    location = tuple(
                        nodes_selectable.loc[
                            ss[nearest_node_key]["Node ID"],
                            ["y", "x"]
                        ]
                    ),
                    tooltip = "Origin",
                    icon = folium.Icon(
                        prefix = "fa",
                        icon = "circle-play",
                        color = "green"
                    )
                )
            
            m1.fit_bounds(
                [[14.565835, 121.014223],
                [14.604602, 121.064785]],
            )

            # search bar
            folium.plugins.Geocoder().add_to(m1)

            col1, col2 = st.columns([3, 1.5])

            with col1:
                map_output = m1.to_streamlit(height = 300, bidirectional=True) # leafmap.foliumap has builtin support for st_folium, by setting bidirectional=True

            pt = map_output["last_clicked"]

            if (pt is not None):

                pt_tuple = (pt["lng"], pt["lat"])

                if (pt_tuple != ss[pt_previous_key]):

                    ss[node_was_manually_changed_key] = True

                    point_df = gpd.GeoDataFrame([{"x": pt["lng"], "y": pt["lat"]}])
                    point_df["geometry"] = gpd.points_from_xy(point_df["x"], point_df["y"])

                    nearest_node = point_df.sjoin_nearest(nodes_selectable, how = "left")[["osmid", "x_left", "y_left", "geometry"]].rename({"osmid": "Node ID", "x_left": "Longitude", "y_left": "Latitude"}, axis = 1).iloc[0]

                    ss[nearest_node_key] = nearest_node
                    ss[pt_previous_key] = (pt["lng"], pt["lat"])

                    rerun_all = False
                    if "SELECT_DESTINATION_nearest_node" in ss:
                        if (ss["SELECT_DESTINATION_nearest_node"] is not None):
                            rerun_all = True

                    if rerun_all:
                        if not ss["rerun_just_occurred"]:
                            ss["rerun_just_occurred"] = True
                            st.rerun(scope = "app")
                        # else:
                        #     if ss["rerun_triggerer"] == "Origin":
                        #         ss["rerun_just_occurred"] = False
                    else:
                        if (not ss["rerun_just_occurred"]):
                            st.rerun(scope = "fragment")

            with col2:
                with st.container(border = True):
                    st.markdown("**Chosen Origin:**")
                    if (ss[nearest_node_key] is not None):
                        st.markdown(f"Node ID: {ss[nearest_node_key]['Node ID']}")
                        st.markdown(f"Latitude: {ss[nearest_node_key]['Latitude']}")
                        st.markdown(f"Longitude: {ss[nearest_node_key]['Longitude']}")
                    else:
                        st.warning("Select an origin point by clicking on the map.")

            return None
        

        # for destination
        key_prefix = "SELECT_DESTINATION"

        pt_previous_key = f"{key_prefix}_pt_previous"
        nearest_node_key = f"{key_prefix}_nearest_node"
        node_was_manually_changed_key = f"{key_prefix}_node_was_manually_changed"

        if pt_previous_key not in ss:
            ss[pt_previous_key] = None

        if (nearest_node_key not in ss) or (node_was_manually_changed_key not in ss):
            default_osmid = 12101126578
            ss[nearest_node_key] = {
                "Node ID": default_osmid,
                "Latitude": nodes_selectable.at[default_osmid, "y"],
                "Longitude": nodes_selectable.at[default_osmid, "x"]
            }
            ss[node_was_manually_changed_key] = True

        @st.fragment
        def select_node_DESTINATION():

            key_prefix = "SELECT_DESTINATION"

            pt_previous_key = f"{key_prefix}_pt_previous"
            nearest_node_key = f"{key_prefix}_nearest_node"
            node_was_manually_changed_key = f"{key_prefix}_node_was_manually_changed"

            mapcenter = (14.581912, 121.037947)
            m2 = leafmap.Map(center = mapcenter)

            m2.add_gdf(
                city_geo,
                layer_name = "Mandaluyong",
                style_function = lambda x: {
                    "color": "black",
                    "opacity": 0.5,
                    "fillOpacity": 0.0,
                    "fillColor": "none",
                },
                control = False # this disables toggle
            )

            if ss[nearest_node_key] is not None:

                m2.add_marker(
                    location = tuple(
                        nodes_selectable.loc[
                            ss[nearest_node_key]["Node ID"],
                            ["y", "x"]
                        ]
                    ),
                    tooltip = "Destination",
                    icon = folium.Icon(
                        prefix = "fa",
                        icon = "flag-checkered",
                        color = "red"
                    )
                )

            m2.fit_bounds(
                [[14.565835, 121.014223],
                [14.604602, 121.064785]],
            )

            # search bar
            folium.plugins.Geocoder().add_to(m2)

            col1, col2 = st.columns([3, 1.5])

            with col1:
                map_output = m2.to_streamlit(height = 300, bidirectional=True) # leafmap.foliumap has builtin support for st_folium, by setting bidirectional=True
            
            pt = map_output["last_clicked"]

            if (pt is not None):

                pt_tuple = (pt["lng"], pt["lat"])

                if (pt_tuple != ss[pt_previous_key]):

                    ss[node_was_manually_changed_key] = True

                    point_df = gpd.GeoDataFrame([{"x": pt["lng"], "y": pt["lat"]}])
                    point_df["geometry"] = gpd.points_from_xy(point_df["x"], point_df["y"])

                    nearest_node = point_df.sjoin_nearest(nodes_selectable, how = "left")[["osmid", "x_left", "y_left", "geometry"]].rename({"osmid": "Node ID", "x_left": "Longitude", "y_left": "Latitude"}, axis = 1).iloc[0]

                    ss[nearest_node_key] = nearest_node
                    ss[pt_previous_key] = (pt["lng"], pt["lat"])

                    rerun_all = False
                    if "SELECT_ORIGIN_nearest_node" in ss:
                        if (ss["SELECT_ORIGIN_nearest_node"] is not None):
                            rerun_all = True

                    if rerun_all:
                        if not ss["rerun_just_occurred"]:
                            ss["rerun_just_occurred"] = True
                            st.rerun(scope = "app")
                        # else:
                        #     if ss["rerun_triggerer"] == "Destination":
                        #         ss["rerun_just_occurred"] = False
                    else:
                        if (not ss["rerun_just_occurred"]):
                            st.rerun(scope = "fragment")

            with col2:
                with st.container(border = True):
                    st.markdown("**Chosen Destination:**")
                    if (ss[nearest_node_key] is not None):
                        st.markdown(f"Node ID: {ss[nearest_node_key]['Node ID']}")
                        st.markdown(f"Latitude: {ss[nearest_node_key]['Latitude']}")
                        st.markdown(f"Longitude: {ss[nearest_node_key]['Longitude']}")
                    else:
                        st.warning("Select a destination point by clicking on the map.")

            return None
        
        if "node_type" not in ss:
            ss["node_type"] = "Origin"

        col1, col2, empty = st.columns([1, 1, 4])

        with col1:
        
            if st.button("Origin"):
                if ss["node_type"] == "Destination":
                    ss["node_type"] = "Origin"

        with col2:

            if st.button("Destination"):
                if ss["node_type"] == "Origin":
                    ss["node_type"] = "Destination"

        node_type = ss["node_type"]

        if node_type == "Origin":
            select_node_ORIGIN()

        elif node_type == "Destination":
            select_node_DESTINATION()

        if (ss["SELECT_ORIGIN_nearest_node"]) is None or (ss["SELECT_DESTINATION_nearest_node"] is None):
            st.info("Before you can view routes, first select an origin and destination with the maps above.")
            st.stop()
            
        node_o = ss["SELECT_ORIGIN_nearest_node"]["Node ID"]
        node_d = ss["SELECT_DESTINATION_nearest_node"]["Node ID"]

        if node_o == node_d:
            st.warning("Choose two different points as origin and destination.")
            st.stop()


    # Determine path based on beta
    beta_options = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    # cache the masks
    @st.cache_data(ttl = None, max_entries=10)
    def get_edge_masks(node_o, node_d, mode):
        result = {}
        for beta in beta_options:
            path_nodes = routes_dict[beta][f"{node_o}, {node_d}"]
            pairs = set([(path_nodes[i], path_nodes[i+1]) for i in range(0, len(path_nodes) - 1)])

            edge_index_frame = edges.index.to_frame()
            edge_mask = edge_index_frame[["u", "v"]].apply(lambda r: (r['u'], r['v']), axis = 1).isin(pairs)

            result[beta] = edge_mask

        return result

    beta_to_edge_mask = get_edge_masks(node_o, node_d, mode = mode_option)

    # Map with routes

    @st.fragment
    def show_routes_map():

        mapcenter = (14.581912, 121.037947)
        m = leafmap.Map(center = mapcenter)
        
        m.add_gdf(
            city_geo,
            layer_name = "Mandaluyong",
            style_function = lambda x: {
                "color": "black",
                "opacity": 0.5,
                "fillOpacity": 0.0,
                "fillColor": "none",
            },
            control = False # this disables toggle
        )

        # show routes for betas

        style_blue_betas = lambda x: {
            "color": "blue",
            "weight": 10,
            "opacity": 0.5
        }

        style_grayed_betas = lambda x: {
            "color": "gray",
            "weight": 3,
            "opacity": 0.5
        }

        for beta in beta_options:

            show_blue = (beta == 0.0)

            edge_mask = beta_to_edge_mask[beta]

            row = {"beta": beta, "geometry": edges.loc[edge_mask].union_all()}

            gdf = gpd.GeoDataFrame([row], crs = "EPSG:4326")

            m.add_gdf(
                gdf,
                layer_name = f"gray Beta={beta} (NO TOGGLE)",
                style_function = style_grayed_betas,
                control = False,
                show = True
            )

            blue_layer_name = f"Path (Beta={beta})"

            m.add_gdf(
                gdf,
                layer_name = blue_layer_name,
                style_function = style_blue_betas,
                control = True,
                show = show_blue
            )
        # end loop

        m.add_marker(
            location = tuple(nodes_selectable.loc[node_o, ["y", "x"]]),
            tooltip = "Origin",
            icon = folium.Icon(
                prefix = "fa",
                icon = "circle-play",
                color = "green"
            )
        )
        
        m.add_marker(
            location = tuple(nodes_selectable.loc[node_d, ["y", "x"]]),
            tooltip = "Destination",
            icon = folium.Icon(
                prefix = "fa",
                icon = "flag-checkered",
                color = "red",
            ),
        )

        m.fit_bounds(
            [[14.565835, 121.014223],
            [14.604602, 121.064785]],
        )

        # search bar
        folium.plugins.Geocoder().add_to(m)

        m.to_streamlit(height = 400, bidirectional=False)

        ### likely not needed
        # if st.button("Refresh"):
        #     st.rerun(scope = "fragment")

        return None
    
    st.divider()
    
    show_routes = st.toggle(
        "Show Routes",
        value = True
    )

    if show_routes:

        ss["rerun_just_occurred"] = False
    
        show_routes_map()