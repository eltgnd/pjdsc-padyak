# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd

from migs_custom_functions import load_discomfort_score_component_info

#--------------------------------------------

# Variables
ss = st.session_state

# Callable

# Initialize
page_title = 'Recompute Discomfort Scores'
page_icon = ':repeat:'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)

#---------------------------------------------

# Preparations

# BIKING DISCOMFORT

def biking_discomfort(s, weights, weights_main_components, preproc_Gb, details = False):
    """Compute biking discomfort for a row from a dataframe of edges.
    
s: Series. The row.

weights: dict. Keys should be same as column names of dataframe.
"""

    # get variables from other function
    sidewalk_description, has_left_sidewalk_status, has_right_sidewalk_status, is_crossing_status, bicycle_status, cycleway_lane_type, cycleway_description, cycleway_left_lane_type, cycleway_right_lane_type, cycleway_class, cycleway_left_class, cycleway_right_class, parking_left_description, parking_right_description, width_comp, lit_comp, maxspeed_comp, segregated_comp, crossing_tag_comp, edsa_accident_comp, motor_vehicle_comp = preproc_Gb.loc[s.name].values

    #----------
    # DISMOUNT

    # sidewalk_description: is_sidewalk, has_sidewalk
    # note to self: being-a-bike-lane should always be scored negatively

    if bicycle_status == "dismount":

        foot_comp = {
            "yes": -2,
            "designated": -1,
            "use_sidepath": 2,
        }.get(s["foot"], 0)

        # alley_comp replaces footway_comp, service_comp for Gb
        is_alley_status = (s["footway"] == "alley") or (s["service"] == "alley")
        alley_comp = -1 if is_alley_status else 0

        highway_comp = {
            "footway": -4,
            "pedestrian": -3,
            "living_street": -2,
            "path": -1,
            "residential": -0.5,
        }.get(s["highway"], 0)

        # sidewalk
        sidewalk_comp = 0
        if has_left_sidewalk_status:
            sidewalk_comp -= 1
        if has_right_sidewalk_status:
            sidewalk_comp -= 1

        parking_subtags_comp = 0
        parking_subtags_comp += {
            "no": -0.5,
            "half_on_kerb": 1,
            "lane": 0.5
        }.get(parking_left_description, 0)
        parking_subtags_comp += {
            "no": -0.5,
            "half_on_kerb": 1,
            "lane": 0.5
        }.get(parking_right_description, 0)

        # FROM IMAGE DATA
        greenery_ratio_comp = 0
        if pd.notnull(s["FROM_IMAGES_greenery_ratio"]):
            greenery_ratio_comp = s["FROM_IMAGES_greenery_ratio"] - 1

        # other that weren't considered for dismount
        bicycle_comp = 0
        cycleway_class_comp = 0
        cycleway_lane_type_comp = 0
        cycling_lane_coverage_comp = 0
        has_bicycle_comp = 0
        road_condition_comp = 0

    # -------
    # NON-DISMOUNT, can ride bike

    # elif bicycle_status in ("yes", "permissive", "destination", "no"):
    else:

        bicycle_comp = {
            "yes": -3,
            "permissive": -2,
            "destination": -1,
            # note that "no" here is not the actual value "no" but the default value for the bicycle info variable
        }.get(bicycle_status, 0)
        # check actual value of bicycle
        if s["bicycle"] == "no":
            bicycle_comp = 3

        cycleway_class_comp = 0
        cycleway_class_comp += {
            "class 3": -1,
            "class 2": -2,
            "class 1": -4,
            "unknown_but_one_of_the_two_must_exist": -1
        }.get(cycleway_left_class, 0)
        cycleway_class_comp += {
            "class 3": -1,
            "class 2": -2,
            "class 1": -4,
            "unknown_but_one_of_the_two_must_exist": -1
        }.get(cycleway_right_class, 0)

        cycleway_lane_type_comp = 0
        cycleway_lane_type_comp += {
            "lane": -1,
            "shared_lane": 1,
            "unknown_but_one_of_the_two_must_exist": -1
        }.get(cycleway_left_lane_type, 0)
        cycleway_lane_type_comp += {
            "lane": -1,
            "shared_lane": 1,
            "unknown_but_one_of_the_two_must_exist": -1
        }.get(cycleway_right_lane_type, 0)

        foot_comp = {
            "yes": 1,
            "designated": 2,
        }.get(s["foot"], 0)

        # alley_comp replaces footway_comp, service_comp for Gb
        is_alley_status = (s["footway"] == "alley") or (s["service"] == "alley")
        alley_comp = 1 if is_alley_status else 0

        highway_comp = {
            "footway": -2,
            "pedestrian": -3,
            "living_street": -4,
            "path": -1,
            "residential": -0.5,
        }.get(s["highway"], 0)

        parking_subtags_comp = 0
        parking_subtags_comp += {
            "no": -1,
            "half_on_kerb": 0.5,
            "lane": 1
        }.get(parking_left_description, 0)
        parking_subtags_comp += {
            "no": -1,
            "half_on_kerb": 0.5,
            "lane": 1
        }.get(parking_right_description, 0)

        # FROM IMAGE DATA
        cycling_lane_coverage_comp = 0
        if pd.notnull(s["FROM_IMAGES_cycling_lane_coverage"]):
            cycling_lane_coverage_comp = s["FROM_IMAGES_cycling_lane_coverage"] - 1 # Subtract 1 because range is 0-1. Should be negative.
        
        greenery_ratio_comp = 0
        if pd.notnull(s["FROM_IMAGES_greenery_ratio"]):
            greenery_ratio_comp = s["FROM_IMAGES_greenery_ratio"] - 1

        has_bicycle_comp = 0
        if pd.notnull(s["FROM_IMAGES_has_bicycle"]):
            greenery_ratio_comp = s["FROM_IMAGES_has_bicycle"] - 1

        road_condition_comp = 0
        if pd.notnull(s["FROM_IMAGES_road_condition"]):
            road_condition_comp = (s["FROM_IMAGES_road_condition"] - 1)

        # other that weren't considered for non-dismount
        sidewalk_comp = 0

    #---
    # final part

    dismount_comp = 10 if bicycle_status == "dismount" else 0

    subcomponent_dict_UNWEIGHTED = {
        "bicycle": bicycle_comp,
        "CYCLEWAY_CLASS": cycleway_class_comp,
        "CYCLEWAY_LANE_TYPE": cycleway_lane_type_comp,
        "foot": foot_comp,
        "highway": highway_comp,
        "ALLEY": alley_comp,
        "width": width_comp,
        "lit": lit_comp,
        "maxspeed": maxspeed_comp,
        "segregated": segregated_comp,
        "sidewalk": sidewalk_comp,
        "PARKING_SUBTAGS": parking_subtags_comp,
        "TAG_crossing": crossing_tag_comp,
        "EDSA_accident_component": edsa_accident_comp,
        "motor_vehicle": motor_vehicle_comp,

        # FROM IMAGE DATA
        "FROM_IMAGES_cycling_lane_coverage": cycling_lane_coverage_comp,
        "FROM_IMAGES_greenery_ratio": greenery_ratio_comp,
        "FROM_IMAGES_has_bicycle": has_bicycle_comp,
        "FROM_IMAGES_road_condition": road_condition_comp,
    }

    subcomponent_dict_WEIGHTED = {subcomponent_name: (value * weights.get(subcomponent_name, 1))
                                  for subcomponent_name, value in subcomponent_dict_UNWEIGHTED.items()}
    subcomponent_dict_WEIGHTED["DISMOUNT"] = dismount_comp

    main_component_dict_UNWEIGHTED_reference = {
        # the ff are based on the Feature groupings document
        "DISMOUNT": ("DISMOUNT", ),
        "convenience": ("bicycle", "ALLEY", "segregated", "PARKING_SUBTAGS", "foot", "FROM_IMAGES_road_condition"),
        "attractiveness": ("FROM_IMAGES_greenery_ratio", ),
        "traffic_safety": ("CYCLEWAY_CLASS", "CYCLEWAY_LANE_TYPE", "FROM_IMAGES_cycling_lane_coverage", "width", "maxspeed"),
        "security": ("lit", "FROM_IMAGES_has_bicycle"),

        # the ff are additional main components added in order to be able to use all of the subcomponents
        "accident_risk": ("EDSA_accident_component", ),
        "traffic_volume": ("highway", "motor_vehicle"),
        "safety_of_sidewalks_and_crossings": ("sidewalk", "TAG_crossing"),
    }

    main_component_dict_UNWEIGHTED = {
        key: sum([subcomponent_dict_WEIGHTED[subcomp] for subcomp in l]) # take the sum of the WEIGHTED versions of the subcomponents, in order to get the UNweighted main component.
        for key, l
        in main_component_dict_UNWEIGHTED_reference.items()
    }

    main_component_dict_WEIGHTED = {main_component_name: value * weights_main_components[main_component_name] for main_component_name, value in main_component_dict_UNWEIGHTED.items()}

    score1 = sum(main_component_dict_WEIGHTED.values())
    score2 = sum(subcomponent_dict_WEIGHTED.values())

    # breakdown_dict = {
    #     "subcomponent_dict_WEIGHTED": subcomponent_dict_WEIGHTED,
    #     "subcomponent_dict_UNWEIGHTED": subcomponent_dict_UNWEIGHTED,
    #     "main_component_dict_WEIGHTED": main_component_dict_WEIGHTED,
    #     "main_component_dict_UNWEIGHTED": main_component_dict_UNWEIGHTED
    # }

    output_dict = {
        "score_weighted_by_main": score1,
        "score_weighted_by_sub": score2,
        # "breakdown_dict": breakdown_dict
    }

    if details:
        output_dict.update({f"SW_{key}": value for key, value in subcomponent_dict_WEIGHTED.items()})
        output_dict.update({f"SU_{key}": value for key, value in subcomponent_dict_UNWEIGHTED.items()})
        output_dict.update({f"MW_{key}": value for key, value in main_component_dict_WEIGHTED.items()})
        output_dict.update({f"MU_{key}": value for key, value in main_component_dict_UNWEIGHTED.items()})

    output = pd.Series(output_dict)

    return output

# WALKING DISCOMFORT

def walking_discomfort(s, weights, weights_main_components, preproc_Gw, details = False):
    """Compute walking discomfort for a row from a dataframe of edges.
    
s: Series. The row.

weights: dict. Keys should be same as column names of dataframe.
"""

    # get variables from other function
    sidewalk_description, has_left_sidewalk_status, has_right_sidewalk_status, is_crossing_status, bicycle_status, cycleway_lane_type, cycleway_description, cycleway_left_lane_type, cycleway_right_lane_type, cycleway_class, cycleway_left_class, cycleway_right_class, parking_left_description, parking_right_description, width_comp, lit_comp, maxspeed_comp, segregated_comp, crossing_tag_comp, edsa_accident_comp, motor_vehicle_comp = preproc_Gw.loc[s.name].values

    foot_comp = {
        "yes": -2,
        "designated": -1,
        "use_sidepath": 2,
    }.get(s["foot"], 0)

    # alley_comp replaces footway_comp, service_comp for Gb
    is_alley_status = (s["footway"] == "alley") or (s["service"] == "alley")
    alley_comp = -1 if is_alley_status else 0

    highway_comp = {
        "footway": -4,
        "pedestrian": -3,
        "living_street": -2,
        "path": -1,
        "residential": -0.5,
        "steps": 1,
    }.get(s["highway"], 0)

    # sidewalk
    sidewalk_comp = 0
    if has_left_sidewalk_status:
        sidewalk_comp -= 1
    if has_right_sidewalk_status:
        sidewalk_comp -= 1

    parking_subtags_comp = 0
    parking_subtags_comp += {
        "no": -0.5,
        "half_on_kerb": 1,
        "lane": 0.5
    }.get(parking_left_description, 0)
    parking_subtags_comp += {
        "no": -0.5,
        "half_on_kerb": 1,
        "lane": 0.5
    }.get(parking_right_description, 0)

    # FROM IMAGE DATA

    sidewalk_ratio_comp = 0
    if pd.notnull(s["FROM_IMAGES_sidewalk_ratio"]):
        sidewalk_ratio_comp = s["FROM_IMAGES_sidewalk_ratio"] - 1
    
    greenery_ratio_comp = 0
    if pd.notnull(s["FROM_IMAGES_greenery_ratio"]):
        greenery_ratio_comp = s["FROM_IMAGES_greenery_ratio"] - 1

    # has_traffic_sign_comp = 0
    # if pd.notnull(s["FROM_IMAGES_has_traffic_sign"]):
    #     has_traffic_sign_comp = (s["FROM_IMAGES_has_traffic_sign"] - 1) * 0.5

    road_condition_comp = 0
    if pd.notnull(s["FROM_IMAGES_road_condition"]):
        road_condition_comp = (s["FROM_IMAGES_road_condition"] - 1)

    has_traffic_light_comp = 0
    if pd.notnull(s["FROM_IMAGES_has_traffic_light"]):
        has_traffic_light_comp = (s["FROM_IMAGES_has_traffic_light"] - 1) * 0.5

    has_crosswalk_comp = 0
    if pd.notnull(s["FROM_IMAGES_has_crosswalk"]):
        has_crosswalk_comp = (s["FROM_IMAGES_has_crosswalk"] - 1)

    obstruction_density_comp = 0
    if pd.notnull(s["FROM_IMAGES_obstruction_density"]):
        obstruction_density_comp = (s["FROM_IMAGES_obstruction_density"] - 1)


    subcomponent_dict_UNWEIGHTED = {
        "foot": foot_comp,
        "highway": highway_comp,
        "ALLEY": alley_comp,
        "width": width_comp,
        "lit": lit_comp,
        "maxspeed": maxspeed_comp,
        "segregated": segregated_comp,
        "sidewalk": sidewalk_comp,
        "PARKING_SUBTAGS": parking_subtags_comp,
        "TAG_crossing": crossing_tag_comp,
        "EDSA_accident_component": edsa_accident_comp,
        "motor_vehicle": motor_vehicle_comp,

        # FROM IMAGE DATA
        "FROM_IMAGES_sidewalk_ratio": sidewalk_ratio_comp,
        "FROM_IMAGES_greenery_ratio": greenery_ratio_comp,
        # "FROM_IMAGES_has_traffic_sign": has_traffic_sign_comp,
        "FROM_IMAGES_road_condition": road_condition_comp,
        "FROM_IMAGES_has_traffic_light": has_traffic_light_comp,
        "FROM_IMAGES_has_crosswalk": has_crosswalk_comp,
        "FROM_IMAGES_obstruction_density": obstruction_density_comp,
    }

    subcomponent_dict_WEIGHTED = {subcomponent_name: value * weights[subcomponent_name] for subcomponent_name, value in subcomponent_dict_UNWEIGHTED.items()}

    main_component_dict_UNWEIGHTED_reference = {
        # the ff are based on the Feature groupings document
        "convenience": ("ALLEY", "foot", "segregated", "PARKING_SUBTAGS",
                        "FROM_IMAGES_obstruction_density", "FROM_IMAGES_road_condition",),
        "traffic_volume": ("highway", "motor_vehicle"),
        "traffic_speed": ("width", "maxspeed", "FROM_IMAGES_has_traffic_light"),
        "attractiveness": ("FROM_IMAGES_greenery_ratio", ),

        # the ff are additional main components added in order to be able to use all of the subcomponents
        "accident_risk": ("EDSA_accident_component", ),
        "safety_of_sidewalks": ("sidewalk", "FROM_IMAGES_sidewalk_ratio", "lit"),
        "safety_of_crossings": ("TAG_crossing", "FROM_IMAGES_has_crosswalk")
    }

    main_component_dict_UNWEIGHTED = {
        key: sum([subcomponent_dict_WEIGHTED[subcomp] for subcomp in l]) # take the sum of the WEIGHTED versions of the subcomponents, in order to get the UNweighted main component.
        for key, l
        in main_component_dict_UNWEIGHTED_reference.items()
    }

    main_component_dict_WEIGHTED = {main_component_name: value * weights_main_components[main_component_name] for main_component_name, value in main_component_dict_UNWEIGHTED.items()}

    score1 = sum(main_component_dict_WEIGHTED.values())
    score2 = sum(subcomponent_dict_WEIGHTED.values())

    # breakdown_dict = {
    #     "subcomponent_dict_WEIGHTED": subcomponent_dict_WEIGHTED,
    #     "subcomponent_dict_UNWEIGHTED": subcomponent_dict_UNWEIGHTED,
    #     "main_component_dict_WEIGHTED": main_component_dict_WEIGHTED,
    #     "main_component_dict_UNWEIGHTED": main_component_dict_UNWEIGHTED
    # }

    output_dict = {
        "score_weighted_by_main": score1,
        "score_weighted_by_sub": score2,
        # "breakdown_dict": breakdown_dict
    }

    if details:

        output_dict.update({f"SW_{key}": value for key, value in subcomponent_dict_WEIGHTED.items()})
        output_dict.update({f"SU_{key}": value for key, value in subcomponent_dict_UNWEIGHTED.items()})
        output_dict.update({f"MW_{key}": value for key, value in main_component_dict_WEIGHTED.items()})
        output_dict.update({f"MU_{key}": value for key, value in main_component_dict_UNWEIGHTED.items()})

    output = pd.Series(output_dict)

    return output

# Load data

@st.cache_data(ttl = None, max_entries = 1)
def load_preproc():
    preproc_Gb = pd.read_csv("migs_pages_data/preproc_Gb.csv").set_index(["u", "v", "key"], drop = True)
    preproc_Gw = pd.read_csv("migs_pages_data/preproc_Gw.csv").set_index(["u", "v", "key"], drop = True)

    return preproc_Gb, preproc_Gw


@st.cache_data(ttl = None, max_entries = 1)
def load_nodes_and_edges():
    folder = "migs_pages_data/"

    Gb_edges = gpd.read_feather(folder + "Gb_edges.feather")
    Gb_nodes = gpd.read_feather(folder + "Gb_nodes.feather")
    Gw_edges = gpd.read_feather(folder + "Gw_edges.feather")
    Gw_nodes = gpd.read_feather(folder + "Gw_nodes.feather")

    return Gb_edges, Gb_nodes, Gw_edges, Gw_nodes


#----------------------------------------------

# Main

if __name__ == "__main__":

    # SESSION STATE

    default_weights_subcomponents_bike_CYCLE, default_weights_subcomponents_bike_DISMOUNT, default_weights_main_components_bike, default_weights_subcomponents_walk, default_weights_main_components_walk, subcomponent_name_to_display_info, bike_main_component_name_to_display_info, walk_main_component_name_to_display_info = load_discomfort_score_component_info()

    if "weights_sub_bike_CYCLE" not in ss:
        ss["weights_sub_bike_CYCLE"] = default_weights_subcomponents_bike_CYCLE
    if "weights_sub_bike_DISMOUNT" not in ss:
        ss["weights_sub_bike_DISMOUNT"] = default_weights_subcomponents_bike_DISMOUNT
    if "weights_main_bike" not in ss:
        ss["weights_main_bike"] = default_weights_main_components_bike
    if "weights_sub_walk" not in ss:
        ss["weights_sub_walk"] = default_weights_subcomponents_walk
    if "weights_main_walk" not in ss:
        ss["weights_main_walk"] = default_weights_main_components_walk
    if "subcomp_info" not in ss:
        ss["subcomp_info"] = subcomponent_name_to_display_info
    if "bike_maincomp_info" not in ss:
        ss["b_maincomp_info"] = bike_main_component_name_to_display_info
    if "walk_maincomp_info" not in ss:
        ss["w_maincomp_info"] = walk_main_component_name_to_display_info

    # additional
    if ("preproc_Gb" not in ss) or ("preproc_Gw" not in ss):
        preproc_Gb, preproc_Gw = load_preproc()
        ss["preproc_Gb"] = preproc_Gb
        ss["preproc_Gw"] = preproc_Gw

    if any([key not in ss for key in ["Gb_edges", "Gb_nodes", "Gw_edges", "Gw_nodes"]]):
        Gb_edges, Gb_nodes, Gw_edges, Gw_nodes = load_nodes_and_edges()
        # Gb_edges["PROGRESS_PERCENTAGE"] = [x / Gb_edges.shape[0] for x in range(Gb_edges.shape[0])]
        # Gw_edges["PROGRESS_PERCENTAGE"] = [x / Gw_edges.shape[0] for x in range(Gw_edges.shape[0])]

        ss["Gb_edges"] = Gb_edges
        ss["Gb_nodes"] = Gb_nodes
        ss["Gw_edges"] = Gw_edges
        ss["Gw_nodes"] = Gw_nodes

    # PAGE FEATURES

    st.markdown("# Recompute Discomfort Scores")

    if st.button("Go"):
        which = "walking"

        progressbar = st.progress(0, text = f"Recomputing {which} discomfort...")

        if which == "cycling":

            entries = []
            counter = -1
            for index, s in ss["Gb_edges"].iterrows():
                counter += 1

                is_dismount = (ss["preproc_Gb"].loc[s.name]["bicycle_status"] == "dismount")

                if (counter % 1000) == 0:
                    rounded_perc = int(round(counter / ss["Gb_edges"].shape[0] * 100, 0))
                    progressbar.progress(rounded_perc, text = f"Recomputing {which} discomfort... {rounded_perc}%")

                score = biking_discomfort(
                    s,
                    weights = ss["weights_sub_bike_DISMOUNT"] if is_dismount else ss["weights_sub_bike_CYCLE"],
                    weights_main_components = ss["weights_main_bike"],
                    preproc_Gb = ss["preproc_Gb"]
                )["score_weighted_by_main"]
            
                entries.append(score)

            progressbar.progress(rounded_perc, text = f"Recomputing {which} discomfort... 100%")
            
            result = pd.Series(entries, index = ss["Gb_edges"].index)
            ss["Gb_edges_discomfort"] = result
            
        elif which == "walking":

            entries = []
            counter = -1
            for index, s in ss["Gw_edges"].iterrows():
                counter += 1

                if (counter % 1000) == 0:
                    rounded_perc = int(round(counter / ss["Gw_edges"].shape[0] * 100, 0))
                    progressbar.progress(rounded_perc, text = f"Recomputing {which} discomfort... {rounded_perc}%")

                score = walking_discomfort(
                    s,
                    weights = ss["weights_sub_walk"],
                    weights_main_components = ss["weights_main_walk"],
                    preproc_Gw = ss["preproc_Gw"]
                )["score_weighted_by_main"]
            
                entries.append(score)

            progressbar.progress(rounded_perc, text = f"Recomputing {which} discomfort... 100%")
            
            result = pd.Series(entries, index = ss["Gw_edges"].index)
            ss["Gw_edges_discomfort"] = result

            # TEST ONLY
            st.write(ss["Gw_edges_discomfort"].mean())