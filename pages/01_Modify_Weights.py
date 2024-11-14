# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt

from discomfort_score_metadata import load_discomfort_score_component_info

# Variables
ss = st.session_state

# Callable

# Initialize
page_title = 'Modify Weights for Discomfort Score'
page_icon = ':pencil:'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)

# preparations


@st.cache_data(ttl = None)
def make_chart_for_subcomponent(subcomp_name, subcomp_group):
    d = ss["subcomp_info"][subcomp_name]
    levels_dict = d.get("levels_ALL", d.get(f"levels_{subcomp_group}", None))

    reverse_df = pd.Series({value: ", ".join([f"'{key}'" for key in levels_dict if levels_dict[key] == value]) for value in levels_dict.values()})
    reverse_df.index.name = "Score"
    reverse_df.name = "Levels"
    reverse_df = reverse_df.reset_index(drop = False)
    reverse_df["Zero"] = 0
    reverse_df["Levels_Display"] = reverse_df["Levels"].str.replace(", ", r"\n")

    xlim_left = min([-0.25, reverse_df["Score"].min() - 0.25])
    xlim_right = max([0.25, reverse_df["Score"].max() + 0.25])

    base = alt.Chart(
        reverse_df
    ).mark_point(
        filled = True,
        size = 800,
        color = "blue",
        opacity = 1
    ).encode(
        x = alt.X("Score:Q", title = f"Effect on Discomfort Score", scale = alt.Scale(domain = [xlim_left, xlim_right])),
        y = alt.Y("Zero:Q", scale=alt.Scale(domain=[-1, 1])),
        tooltip = ["Levels", "Score"]
    )

    text_of_levels = base.mark_text(
        dy=-30,
        lineBreak=r'\n',
        baseline = "line-bottom",
        align = "left",
        angle = 345,
        size=13
    ).encode(
        text = "Levels_Display:N",
    )

    text_in_points = base.mark_text(
        dy=0,
        lineBreak=r'\n',
        baseline = "middle",
        align = "center",
        angle = 0,
        size=13,
        color = "white",
    ).encode(
        text = alt.Text("Score:Q", format = "+", formatType = "number"),
    )

    red_point = alt.Chart().mark_point(color = "darkred", filled = True, tooltip = False, size = 800, opacity = 1).encode(x=alt.datum(0), y = alt.datum(0))

    hline = alt.Chart(reverse_df).mark_rule(color = "black", strokeWidth = 3, tooltip = False).encode(y = alt.datum(0))

    vline = alt.Chart(reverse_df).mark_rule(strokeDash = [6,5], strokeWidth = 3, color = "darkred", tooltip = False).encode(x = alt.datum(0), y = alt.datum(-0.7), y2 = alt.datum(0))

    vline_text = vline.mark_text(
        dy = 10, color = "darkred", tooltip = False, size = 12, lineBreak=r'\n',
    ).encode(
        text = alt.datum(r"Zero effect\n(default when unspecified)")
    )

    chart = (hline + vline + base + red_point + text_in_points + text_of_levels + vline_text
    ).configure_axisX(
        tickMinStep = 0.5,
        format = "+", # numbers should be signed
        formatType = "number",
        labelFontSize = 15,
        grid = True
    ).configure_axisY(
        disable = True,
    ).properties(
        width=450,
        height=250
    )

    return chart

@st.cache_data
def show_expander_for_subcomp(subcomp_name, exp_title, subcomp_group):
    with st.expander(exp_title, expanded = False):

        d = ss["subcomp_info"][subcomp_name]

        st.markdown(f"### {d['display_name']}")
        st.markdown(d['description'])

        levels_dict = d.get("levels_ALL", d.get(f"levels_{subcomp_group}", None))
            
        if levels_dict is not None:

            with st.container(border = True):
                st.altair_chart(make_chart_for_subcomponent(subcomp_name, subcomp_group))

            if "extra_explanation" in d:
                st.caption(d['extra_explanation'])

    return None

def generate_terms_of_formula(d, ss_weights_key):
    to_concat = []

    for subcomp_name in d['subcomponents']:

        if subcomp_name in ss[ss_weights_key]:

            subcomp_display_name = subcomponent_name_to_display_info[subcomp_name]["display_name"]

            subcomp_weight = round(ss[ss_weights_key][subcomp_name], 2)

            current_term = f"(**{round(subcomp_weight, 2)}** x {subcomp_display_name})"

            prefix = "" if len(to_concat) == 0 else "+ "

            to_concat.append(prefix + current_term)

            result = "\n\n".join(to_concat)

    return result

def update_weights_dict_from_key(sskey_weights_TEMP, component_name, data_key):
    ss[sskey_weights_TEMP][component_name] = ss[data_key]
    return None

# Main

if __name__ == "__main__":
    st.markdown("# Modify Weights for Discomfort Score")

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

    mode_option = st.radio(
        "Mode of active transport",
        options = ["Cycling", "Walking"],
        horizontal = True,
    )

    if mode_option == "Cycling":
        maincomp_info_reference = ss["b_maincomp_info"]
        sskey_main_weights = "weights_main_bike"

    elif mode_option == "Walking":
        maincomp_info_reference = ss["w_maincomp_info"]
        sskey_main_weights = "weights_main_walk"

    if (mode_option == "Walking"):

        tab_main, tab_sub = st.tabs([f":one: Main Components", f":two: Subcomponents"])

        with tab_sub:
                
            for subcomp_name, d in ss["subcomp_info"].items():

                feature_is_relevant = "WALK" in d["INCLUDE_IN"]

                if feature_is_relevant:

                    exp_title = f"{d['display_name']}"

                    col1, col2 = st.columns([1, 3])

                    with col1:
                        this_key = f"CHANGE_WEIGHTS_walk_SUB_{subcomp_name}"
                        result = st.number_input(
                            this_key,
                            value = float(ss["weights_sub_walk"][subcomp_name]),
                            step = 0.1,
                            key = this_key,
                            label_visibility = "collapsed", # necessary to remove the space above the input box that is left by the empty label
                            on_change = update_weights_dict_from_key,
                            args = ("weights_sub_walk", subcomp_name, this_key)
                        )

                        # ### FOR VERIFICATION
                        # st.write(ss["weights_sub_walk"][subcomp_name])

                    with col2:
                        show_expander_for_subcomp(subcomp_name, exp_title, subcomp_group="WALK")

    elif (mode_option == "Cycling"):

        tab_main, tab_sub_cycle, tab_sub_dismount = st.tabs([f":one: Main Components", f":two: Subcomponents (Cycleable Paths)", f":three: Subcomponents (Dismount)"])

        with tab_sub_cycle:

            st.info("These are the subcomponents describing paths where **cycling is permitted**.", icon = "❗")

            for subcomp_name, d in ss["subcomp_info"].items():

                feature_is_relevant = "CYCLE" in d["INCLUDE_IN"]

                if feature_is_relevant:

                    exp_title = f"{d['display_name']}"

                    col1, col2 = st.columns([1, 3])

                    with col1:
                        this_key = f"CHANGE_WEIGHTS_bike_CYCLE_SUB_{subcomp_name}"
                        result = st.number_input(
                            this_key,
                            # value = float(ss["weights_sub_bike_CYCLE"][subcomp_name]),
                            value = float(default_weights_subcomponents_bike_CYCLE[subcomp_name]),
                            step = 0.1,
                            key = this_key,
                            label_visibility = "collapsed", # necessary to remove the space above the input box that is left by the empty label
                            on_change = update_weights_dict_from_key,
                            args = ("weights_sub_bike_CYCLE", subcomp_name, this_key)
                        )

                        # ### FOR VERIFICATION
                        # st.write(ss["weights_sub_bike_CYCLE"][subcomp_name])

                    with col2:
                        show_expander_for_subcomp(subcomp_name, exp_title, subcomp_group="CYCLE")

        with tab_sub_dismount:

            st.info("These are the subcomponents describing **non-cycleable paths**, where cyclists must dismount and push their bikes.", icon = "❗")

            for subcomp_name, d in ss["subcomp_info"].items():

                feature_is_relevant = "DISMOUNT" in d["INCLUDE_IN"]

                if feature_is_relevant:

                    exp_title = f"{d['display_name']}"

                    col1, col2 = st.columns([1, 3])

                    with col1:
                        this_key = f"CHANGE_WEIGHTS_bike_DISMOUNT_SUB_{subcomp_name}"
                        result = st.number_input(
                            this_key,
                            # value = float(ss["weights_sub_bike_DISMOUNT"][subcomp_name]),
                            value = float(default_weights_subcomponents_bike_DISMOUNT[subcomp_name]),
                            step = 0.1,
                            key = this_key,
                            label_visibility = "collapsed", # necessary to remove the space above the input box that is left by the empty label
                            on_change = update_weights_dict_from_key,
                            args = ("weights_sub_bike_DISMOUNT", subcomp_name, this_key)
                        )

                        # ### FOR VERIFICATION
                        # st.write(ss["weights_sub_bike_DISMOUNT"][subcomp_name])

                    with col2:
                        show_expander_for_subcomp(subcomp_name, exp_title, subcomp_group="DISMOUNT")


    # The ff code applies to both Walking and Cycling        
    with tab_main:
        for maincomp_name, d in maincomp_info_reference.items():
            exp_title = f"{d['display_name']}"

            col1, col2 = st.columns([1, 3])

            with col1:

                this_key = f"CHANGE_WEIGHTS_{mode_option}_MAIN_{maincomp_name}"
                result = st.number_input(
                    this_key,
                    value = float(ss[sskey_main_weights][maincomp_name]),
                    step = 0.1,
                    key = this_key,
                    label_visibility = "collapsed", # necessary to remove the space above the input box that is left by the empty label
                    on_change = update_weights_dict_from_key,
                    args = (sskey_main_weights, maincomp_name, this_key),
                )

                # # FOR VERIFICATION
                # st.write(ss[sskey_main_weights][maincomp_name])

            with col2:

                with st.expander(exp_title, expanded = False):
                    st.markdown(f"### {d['display_name']}")
                    st.markdown(d['description'])

                    if 'subcomponents' in d:

                        with st.container(border = True):

                            if mode_option == "Walking":

                                st.caption("Formula:")

                                walk_terms = generate_terms_of_formula(d, "weights_sub_walk")

                                st.markdown(walk_terms)
                                    
                            elif mode_option == "Cycling":

                                CYCLE_terms = generate_terms_of_formula(d, "weights_sub_bike_CYCLE")

                                DISMOUNT_terms = generate_terms_of_formula(d, "weights_sub_bike_DISMOUNT")

                                st.caption("Formula for cycleable paths:")

                                st.markdown(CYCLE_terms)

                                st.divider()

                                st.caption("Formula for non-cycleable paths:")

                                st.markdown(DISMOUNT_terms)

                                st.divider()

                            st.caption("Based on currently set weights of subcomponents. You can change these in the Subcomponents tab.")