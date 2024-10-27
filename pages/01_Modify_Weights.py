# Packages
import streamlit as st

# Variables
ss = st.session_state

# Callable

# Initialize
page_title = 'Modify Weights for Discomfort Score'
page_icon = ':pencil:'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)

# preparations

@st.cache_data(ttl = None, max_entries = 1)
def load_discomfort_score_component_info():
    default_weights_subcomponents_bike = {
        "DISMOUNT": 1,
        "bicycle": 1,
        "CYCLEWAY_CLASS": 1,
        "CYCLEWAY_LANE_TYPE": 1,
        "foot": 1,
        "highway": 1,
        "ALLEY": 1,
        "width": 1,
        "lit": 1,
        "maxspeed": 1,
        "segregated": 1,
        "sidewalk": 1,
        "PARKING_SUBTAGS": 1,
        "TAG_crossing": 1,
        "EDSA_accident_component": 1,
        "motor_vehicle": 1,

        # FROM IMAGE DATA
        "FROM_IMAGES_cycling_lane_coverage": 1,
        "FROM_IMAGES_greenery_ratio": 1,
        "FROM_IMAGES_has_bicycle": 1,
        "FROM_IMAGES_road_condition": 1,
    }

    default_weights_main_components_bike = {
        "DISMOUNT": 1,
        "convenience": 1,
        "attractiveness": 1,
        "traffic_safety": 1,
        "security": 1,

        "accident_risk": 1,
        "traffic_volume": 1,
        "safety_of_sidewalks_and_crossings": 1,
    }

    default_weights_subcomponents_walk = {
        "foot": 1,
        "highway": 1,
        "ALLEY": 1,
        "width": 1,
        "lit": 1,
        "maxspeed": 1,
        "segregated": 1,
        "sidewalk": 1,
        "PARKING_SUBTAGS": 1,
        "TAG_crossing": 1,
        "EDSA_accident_component": 1,
        "motor_vehicle": 1,
        "FROM_IMAGES_sidewalk_ratio": 1,
        "FROM_IMAGES_greenery_ratio": 1,
        "FROM_IMAGES_road_condition": 1,
        "FROM_IMAGES_has_traffic_light": 1,
        "FROM_IMAGES_has_crosswalk": 1,
        "FROM_IMAGES_obstruction_density": 1,
    }

    default_weights_main_components_walk = {
        "convenience": 1,
        "traffic_volume": 1,
        "traffic_speed": 1,
        "attractiveness": 1,
        "accident_risk": 1,
        "safety_of_sidewalks": 1,
        "safety_of_crossings": 1,
    }

    subcomponent_name_to_display_info = {
        # note, levels in this dictionary are not necessarily the same as the string representation of the level in the original dataset. This is intended only for display purposes.
        # the DISMOUNT subcomponent is intentionally left out so that it can be shown only in the main components part.
        "bicycle": {
            "display_name": "Bicycle Access",
            "description": "Cyclist level of access. `destination` means that bicycles have legal right-of-way, but only if their destination is in that street or the immediate area; it is not for cyclist 'through traffic.' Note that even roads labeled `no` may, at times, be used by bikers especially if there is lax implementation of cyclist prohibition in the area.",
            "levels_CYCLE": {
                "yes": -3,
                "permissive": -2,
                "destination": -1,
                "no": 3,
            },
        },
        "CYCLEWAY_CLASS": {
            "display_name": "Bike Lane Class",
            "description": "Philippine bike lane class.",
            "levels_CYCLE": {
                "class 1": -4,
                "class 2": -2,
                "class 3": -1,
            }
        },
        "CYCLEWAY_LANE_TYPE": {
            "display_name": "Shared Bike Lane",
            "description": "Whether the bike lane is shared with motorists or not.",
            "levels_CYCLE": {
                "exclusive lane": -1,
                "shared lane": 1,
            }
        },
        "foot": {
            "display_name": "Foot Path Type",
            "description": "Whether foot traffic is explicitly permitted (`yes`) or this street section is designated mainly for pedestrians (`designated`). In the **pedestrian network**, some roads are marked `use_sidepath`, which means there are times when pedestrians can walk on the road, but they are advised to use a different path on the side.",
            "levels_CYCLE": {
                "yes": 1,
                "designated": 2,
            },
            "levels_DISMOUNT": {
                "yes": -2,
                "designated": -1,
                "use_sidepath": 2,
            },
            "levels_WALK": {
                "yes": -2,
                "designated": -1,
                "use_sidepath": 2,
            },
        },
        "highway": {
            "display_name": "Street Type",
            "description": "The type of street, if it is intended for pedestrians and/or cyclists. In the pedestrian network, paths marked `steps` indicate that one must use stairs, such as stairs at a footbridge.",
            "levels_CYCLE": {
                "living_street": -4,
                "pedestrian": -3,
                "footway": -2,
                "path": -1,
                "residential": -0.5,
            },
            "levels_DISMOUNT": {
                "footway": -4,
                "pedestrian": -3,
                "living_street": -2,
                "path": -1,
                "residential": -0.5,
            },
            "levels_WALK": {
                "footway": -4,
                "pedestrian": -3,
                "living_street": -2,
                "path": -1,
                "residential": -0.5,
                "steps": 1,
            },
        },
        "ALLEY": {
            "display_name": "Alley",
            "description": "Whether or not a street is an alley.",
            "levels_CYCLE": {
                "not alley": 0,
                "alley": 1,
            },
            "levels_DISMOUNT": {
                "alley": -1,
                "not alley": 0,
            },
            "levels_WALK": {
                "alley": -1,
                "not alley": 0,
            },
        },
        "width": {
            "display_name": "Width of Road",
            "description": "Road width in meters. **This subcomponent is calculated as 3 minus the actual road width.** For example, a 3m wide road is scored 0, and a 2m wide road is scored -1.",
        },
        "lit": {
            "display_name": "Presence of Illumination",
            "description": "Whether the street section has a street lamp or is at least illuminated by other artifical sources at night.",
            "levels_ALL": {
                "yes": -1,
                "no": 0
            },
        },
        "maxspeed": {
            "display_name": "Legal Speed Limit",
            "description": "The legal speed limit for motorists on this road.",
            "levels_ALL": {
                "less than 30 km/h": -1,
                "30 km/h": 0,
                "greater than 30 km/h": 1,
            },
        },
        "segregated": {
            "display_name": "Segregation of Path Used by Both Pedestrians and Cyclists",
            "description": "Whether a path used by both pedestrians and cyclists has segregated lanes separating the two.",
            "levels_ALL": {
                "yes": 0,
                "no": 1,
            }
        },
        "sidewalk": {
            "display_name": "Sidewalk Presence beside Road",
            "description": "Whether one, neither, or both of the sides of a road section have a sidewalk. Note this component is set to 0 for streets in the cycling network that permit cycling or have a bike lane, i.e., it does not have an effect on discomfort in that case",
            "levels_ALL": {
                "left side: present": -1,
                "right side: present": -1,
            },
            "is_multi": True, # this means a single street can be affected by multiple of these conditions
        },
        "PARKING_SUBTAGS": {
            "display_name": "Parking Presence beside Road",
            "description": "Whether a road section has parking on or adjacent to it.",
            "levels_CYCLE": {
                "left side: no parking": -1,
                "right side: no parking": -1,
                "left side: parking is half-on-curb": 0.5,
                "right side: parking is half-on-curb": 0.5,
                "left side: parking lane on road": 1,
                "right side: parking lane on road": 1,
            },
            "levels_DISMOUNT": {
                "left side: no parking": -0.5,
                "right side: no parking": -0.5,
                "left side: parking is half-on-curb": 1,
                "right side: parking is half-on-curb": 1,
                "left side: parking lane on road": 0.5,
                "right side: parking lane on road": 0.5,
            },
            "levels_WALK": {
                "left side: no parking": -0.5,
                "right side: no parking": -0.5,
                "left side: parking is half-on-curb": 1,
                "right side: parking is half-on-curb": 1,
                "left side: parking lane on road": 0.5,
                "right side: parking lane on road": 0.5,
            },
            "is_multi": True
        },
        "TAG_crossing": {
            "display_name": "Unmarked/Informal Crosswalk",
            "description": "Whether or not a crosswalk is unmarked/informal.",
            "levels_ALL": {
                "ordinary": 0,
                "unmarked/informal": 1
            }
        },
        "motor_vehicle": {
            "display_name": "Motor vehicle access",
            "description": "Whether motor vehicles may use this section of a street.",
            "levels_ALL": {
                "motor vehicles not permitted": -2,
                "cars not permitted": -1,
            }
        },
        "EDSA_accident_component": {
            "display_name": "Relative accident risk",
            "description": "Relative risk of a motor vehicle accident on the road section. **In the current version**, only sections of EDSA have data on accident risk, based on the number of accidents that occurred on each road section in the most recent available year of data.",
            "levels_ALL": {
                "<= 5 accidents/year": 0,
                "5 - 20 accidents/year": 1,
                ">20 accidents/year": 2,
            }
        },

        # FROM IMAGE DATA
        "FROM_IMAGES_cycling_lane_coverage": {
            "display_name": "Cycling Lane Coverage",
            "description": "For roads with bike lanes, this component reflects the percentage of the road area that is occupied by the bike lane, based on the average from multiple pictures taken on the street. This component is a number between -1 and 0, with a lower number indicating a greater percentage of the road being taken up by the bike lane.",
            "is_computer_vision": True,
            "EXCLUDE_IN_DISMOUNT": True,
            "EXCLUDE_IN_WALK": True,
        },
        "FROM_IMAGES_sidewalk_ratio": {
            "display_name": "Sidewalk Ratio",
            "description": "For roads with sidewalks, this component reflects the area of the sidewalk relative to the road area, based on the average from multiple pictures taken on the street. This component is a number between -1 and 0, with a lower number indicating that the sidewalk occupies more space (relative to the road that it is on).",
            "EXCLUDE_IN_CYCLE": True,
            "EXCLUDE_IN_DISMOUNT": True,
            "is_computer_vision": True,
        },
        "FROM_IMAGES_obstruction_density": {
            "display_name": "Obstruction Density",
            "description": "An estimate of the level of presence of obstructions to pedestrians or cyclists on a street section. This is scored by a decimal between -1 and 0, with a lower number meaning fewer obstructions.",
            "EXCLUDE_IN_CYCLE": True,
            "EXCLUDE_IN_DISMOUNT": True,
            "is_computer_vision": True,
        },
        
        "FROM_IMAGES_greenery_ratio": {
            "display_name": "Greenery Ratio",
            "description": "An estimate of the amount of greenery present, on average, in photos taken on this street. This is scored by a decimal between -1 and 0, with a lower number meaning more greenery.",
            "is_computer_vision": True,
        },
        "FROM_IMAGES_road_condition": {
            "display_name": "Road Condition",
            "description": "Road condition assessed using an image classification model.",
            "levels_ALL": {
                "good condition": -1,
                "poor condition": 0,
            },
            "is_computer_vision": True,
        },
        "FROM_IMAGES_has_crosswalk": {
            "display_name": "Crosswalk Presence on Road",
            "description": "Whether or not photos taken on this street show crosswalks.",
            "levels_ALL": {
                "crosswalk seen in photos": -1,
                "no crosswalks": 0,
            },
            "is_computer_vision": True,
        },
        "FROM_IMAGES_has_bicycle": {
            "display_name": "Cyclist Presence",
            "description": "Whether or not photos taken on this street show any cyclists using it.",
            "levels_CYCLE": {
                "cyclist seen in photos": -1,
                "no cyclists": 0,
            },
            "is_computer_vision": True,
        },
        "FROM_IMAGES_has_traffic_light": {
            "display_name": "Traffic Light Presence",
            "description": "Whether or not photos taken on this street show traffic lights.",
            "levels_WALK": {
                "traffic light seen in photos": -1,
                "no traffic lights": 0,
            },
            "is_computer_vision": True,
        },
    }

    bike_main_component_name_to_display_info = {
        "DISMOUNT": {
            "display_name": "Cycle or Dismount",
            "description": "Whether the biker may cycle on this street section, or must dismount and walk their bike. For example, bikers may not cycle directly on a sidewalk.\n\nBy default (when the weight for this component is set to 1):\n\n- Street sections where cycling is allowed are given 0 additional discomfort.\n\n- Street sections where bikers must dismount are given 10 additional discomfort.",
        },
        "convenience": {
            "display_name": "Convenience",
            "description": "The weighted sum of data describing convenience experienced by bikers.",
            "subcomponents": ("bicycle", "ALLEY", "segregated", "PARKING_SUBTAGS", "foot", "FROM_IMAGES_road_condition"),
        },
        "attractiveness": {
            "display_name": "Attractiveness",
            "description": "The weighted sum of data describing the visual attractiveness of a street. Currently, this considers the relative amount of greenery in each street.",
            "subcomponents": ("FROM_IMAGES_greenery_ratio", ),
        },
        "traffic_safety": {
            "display_name": "Traffic Safety",
            "description": "The weighted sum of data describing traffic safety for cyclists.",
            "subcomponents": ("CYCLEWAY_CLASS", "CYCLEWAY_LANE_TYPE", "FROM_IMAGES_cycling_lane_coverage", "width", "maxspeed"),
        },
        "security": {
            "display_name": "Sense of Security",
            "description": "The weighted sum of street features that affect cyclists' sense of security, such as whether the street is lit by street lamps, and whether cyclists are known to use the street.",
            "subcomponents": ("lit", "FROM_IMAGES_has_bicycle"),
        },

        "accident_risk": {
            "display_name": "Relative accident risk",
            "description": "Risk of a motor vehicle accident on the road section. In the current version, only sections of EDSA have data on accident risk, based on the number of accidents that occurred on each road section in the most recent available year of data.",
            "subcomponents": ("EDSA_accident_component", ),
        },
        "traffic_volume": {
            "display_name": "Traffic Volume's Effect on Sense of Safety",
            "description": "The weighted sum of data indicating the relative volume of traffic on a street.",
            "subcomponents": ("highway", "motor_vehicle"),
        },
        "safety_of_sidewalks_and_crossings": {
            "display_name": "Safety of Sidewalks and Crossings",
            "description": "The weighted sum of data indicating the presence of sidewalks on a street and the safety of crossings.",
            "subcomponents": ("sidewalk", "TAG_crossing"),
        },
    }

    walk_main_component_name_to_display_info = {
        "convenience": {
            "display_name": "Convenience",
            "description": "The weighted sum of data describing convenience experienced by pedestrians.",
            "subcomponents": ("ALLEY", "foot", "segregated", "PARKING_SUBTAGS", "FROM_IMAGES_obstruction_density", "FROM_IMAGES_road_condition",),
        },
        "traffic_volume": {
            "display_name": "Traffic Volume's Effect on Sense of Safety",
            "description": "The weighted sum of data indicating the relative speed of traffic on a street.",
            "subcomponents": ("highway", "motor_vehicle"),
        },
        "traffic_speed": {
            "display_name": "Traffic Speed's Effect on Sense of Safety",
            "description": "The weighted sum of data indicating the relative speed of traffic on a street.",
            "subcomponents": ("width", "maxspeed", "FROM_IMAGES_has_traffic_light"),
        },
        "attractiveness": {
            "display_name": "Attractiveness",
            "description": "The weighted sum of data describing the visual attractiveness of a street. Currently, this considers the relative amount of greenery in each street.",
            "subcomponents": ("FROM_IMAGES_greenery_ratio", ),
        },
        "accident_risk": {
            "display_name": "Relative accident risk",
            "description": "Risk of a motor vehicle accident on the road section. **In the current version**, only sections of EDSA have data on accident risk, based on the number of accidents that occurred on each road section in the most recent available year of data.",
            "subcomponents": ("EDSA_accident_component", ),
        },
        "safety_of_sidewalks": {
            "display_name": "Safety of Sidewalks",
            "description": "The weighted sum of data indicating the presence of sidewalks on a street, the size of the sidewalk relative to the road, and whether the sidewalk is lit by street lamps.",
            "subcomponents": ("sidewalk", "TAG_crossing"),
        },
        "safety_of_crossings": {
            "display_name": "Safety of Crossings",
            "description": "The weighted sum of data indicating whether specific roads have crosswalks, as well as the safety of specific crosswalks.",
            "subcomponents": ("TAG_crossing", "FROM_IMAGES_has_crosswalk")
        },
    }

    return default_weights_subcomponents_bike, default_weights_main_components_bike, default_weights_subcomponents_walk, default_weights_main_components_walk, subcomponent_name_to_display_info, bike_main_component_name_to_display_info, walk_main_component_name_to_display_info

# Main

if __name__ == "__main__":
    st.markdown("# Modify Weights for Discomfort Score")

    default_weights_subcomponents_bike, default_weights_main_components_bike, default_weights_subcomponents_walk, default_weights_main_components_walk, subcomponent_name_to_display_info, bike_main_component_name_to_display_info, walk_main_component_name_to_display_info = load_discomfort_score_component_info()

    if "weights_sub_bike" not in ss:
        ss["weights_sub_bike"] = default_weights_subcomponents_bike
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

    if "CHANGE_WEIGHTS_mode_just_changed" not in ss:
        ss["CHANGE_WEIGHTS_mode_just_changed"] = True

    def on_change_mode():
        ss["CHANGE_WEIGHTS_mode_just_changed"] = True

    mode_option = st.radio(
        "Edit weights for:",
        options = ["Cyclist Discomfort", "Pedestrian Discomfort"],
        horizontal = True,
        on_change = on_change_mode,
    )

    if ss["CHANGE_WEIGHTS_mode_just_changed"] or ("CHANGE_WEIGHTS_mode_just_changed" not in ss):
        if mode_option == "Cyclist Discomfort":
            ss['CHANGE_WEIGHTS_maincomp_info_reference'] = ss["b_maincomp_info"]
            ss['CHANGE_WEIGHTS_sub_weights_reference'] = ss["weights_sub_bike"]
            ss['CHANGE_WEIGHTS_main_weights_reference'] = ss["weights_main_bike"]
    
        elif mode_option == "Pedestrian Discomfort":
            ss['CHANGE_WEIGHTS_maincomp_info_reference'] = ss["w_maincomp_info"]
            ss['CHANGE_WEIGHTS_sub_weights_reference'] = ss["weights_sub_walk"]
            ss['CHANGE_WEIGHTS_main_weights_reference'] = ss["weights_main_walk"]

    # Revert to False
    ss["CHANGE_WEIGHTS_mode_just_changed"] = False

    maincomp_info_reference = ss["CHANGE_WEIGHTS_maincomp_info_reference"]
    main_weights_reference = ss["CHANGE_WEIGHTS_main_weights_reference"]
    sub_weights_reference = ss["CHANGE_WEIGHTS_sub_weights_reference"]

    st.divider()

    tab_main, tab_sub = st.tabs([f":one: Main Components for {mode_option}", f":two: Subcomponents for {mode_option}"])

    with tab_main:
        for maincomp_name, d in maincomp_info_reference.items():
            exp_title = f"{d['display_name']}"

            col1, col2 = st.columns([1, 2])

            with col1:
                st.number_input(
                    "",
                    value = 1.0,
                    step = 0.01,
                    key = f"CHANGE_WEIGHTS_{mode_option}_MAIN_{d['display_name']}",
                    label_visibility = "collapsed" # necessary to remove the space above the input box that is left by the empty label
                )

            with col2:

                with st.expander(exp_title, expanded = False):
                    st.markdown(f"### {d['display_name']}")
                    st.markdown(d['description'])

                    if 'subcomponents' in d:

                        to_concat = []

                        for i, subcomp_name in enumerate(d['subcomponents']):

                            subcomp_display_name = subcomponent_name_to_display_info[subcomp_name]["display_name"]

                            subcomp_weight = round(sub_weights_reference[subcomp_name], 2)

                            current_term = f"({subcomp_weight} x {subcomp_display_name})"

                            prefix = "" if i == 0 else "\+ "

                            to_concat.append(prefix + current_term)

                        with st.container(border = True):
                            st.caption(f"*{d['display_name']} formula*\n\n = " + "\n\n".join(to_concat))
                            st.markdown("Based on currently set weights of subcomponents.")