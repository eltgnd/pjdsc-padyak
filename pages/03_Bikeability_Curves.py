# Packages
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd

#--------------------------------------------

# Variables
ss = st.session_state

# Callable

# Initialize
page_title = 'Bikeability Curves'
page_icon = ':city_sunrise:'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)

#---------------------------------------------

# Preparations

@st.cache_data(ttl = None, max_entries = 1)
def load_curve_data():
    brgy_bike_results = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_bike_results.csv")
    brgy_walk_results = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_walk_results.csv")

    brgy_bike_metrics = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_bike_metrics.csv").set_index("adm4_pcode", drop = False).sort_values("adm4_en", ascending=True)
    brgy_walk_metrics = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_walk_metrics.csv").set_index("adm4_pcode", drop = False).sort_values("adm4_en", ascending=True)

    city_bike_results = pd.read_csv("migs_pages_data/city_curve_analysis/city_bike_results.csv")
    city_walk_results = pd.read_csv("migs_pages_data/city_curve_analysis/city_walk_results.csv")

    city_bike_metrics = city_bike_results.drop("beta", axis = 1).mean(axis = 0)
    city_walk_metrics = city_walk_results.drop("beta", axis = 1).mean(axis = 0)

    return brgy_bike_results, brgy_walk_results, brgy_bike_metrics, brgy_walk_metrics, city_bike_results, city_walk_results, city_bike_metrics, city_walk_metrics

def tradeoff_rate(r1, r2):
    dist_change_percent = 100 * ((r2["relative_distance"] / r1["relative_distance"]) - 1)
    discomfort_change_percent = 100 * (1 - (r2["relative_discomfort"] / r1["relative_discomfort"]))

    # also computing these for reference
    dist_change_exact = abs(r2["relative_distance"] - r1["relative_distance"])
    discomfort_change_exact = abs(r2["relative_discomfort"] - r1["relative_discomfort"])

    if dist_change_percent != 0:
        tor = abs( discomfort_change_percent / dist_change_percent )
    else:
        tor = np.nan
    
    return tor, dist_change_percent, discomfort_change_percent, dist_change_exact, discomfort_change_exact

def tradeoff_rates_from_results(results):
    new_rows = []
    results_df = results.sort_values("beta", ascending = True).reset_index(drop = True)
    max_index = results_df.shape[0] - 1

    new_rows.append({
        "higher_beta": results_df.loc[0]["beta"],
        "tradeoff_rate": "not applicable",
        "text_display": "",
    })

    for i, row1 in results_df.iterrows():
        if i+1 <= max_index:
            row2 = results_df.loc[i+1]
            beta_pair = f'Beta={row1["beta"]} to Beta={row2["beta"]}'
            tor, dist_change_percent, discomfort_change_percent, dist_change_exact, discomfort_change_exact = tradeoff_rate(row1, row2)
            rounded_tor = round(tor, 2)
            new_row = {
                "lower_beta": row1["beta"],
                "higher_beta": row2["beta"],
                "beta_pair": beta_pair,
                "relative_distance_PREVIOUS": row1["relative_distance"],
                "relative_discomfort_PREVIOUS": row1["relative_discomfort"],
                "tradeoff_rate": tor,
                "tradeoff_rate_rounded": rounded_tor,
                "distance_change_percent": dist_change_percent,
                "discomfort_change_percent": discomfort_change_percent,
                "distance_change_exact": dist_change_exact,
                "discomfort_change_exact": discomfort_change_exact,
                "text_display": fr"MTOR = {rounded_tor}", # modified TOR
            }
            new_rows.append(new_row)

    tor_df = pd.DataFrame(new_rows)
    return tor_df

def display_explanation_expander():
    with st.expander("Explanations of Metrics", expanded=False):
        st.markdown("""- Relative Distance (Circuity) is given by the distance of the best path, divided by the straight-line distance between the origin and destination. It is always greater than or equal to 1. A value of 2, for example, means that the route taken from point A to point B is twice as long as the straight-line distance between A and B.

- Relative Discomfort is given by the total discomfort of the best path, divided by the distance of that path. It can be interpreted as the rate at which discomfort is experienced for every meter travelled.
                    
- For different values of Beta (sensitivity to discomfort), the optimal path between any two given locations in the city changes; thus the Relative Distance and Relative Discomfort also change.
                                            
- MTOR (Modified Trade-off Rate) is given by the proportion decrease in relative discomfort, divided by the proportion increase in relative distance. This correlates with the slope of the graph, though it is not equal to slope. Higher MTOR is better because it indicates that a relatively short detour can improve comfort greatly.""")

def display_single_area_analysis(city_metrics, city_results, place_name):

    tor_df = tradeoff_rates_from_results(city_results)

    city_results = city_results.merge(tor_df, left_on = "beta", right_on="higher_beta", how = "left")

    # if both relative discomfort and relative distance had a very small change, drop duplicates.
    city_results["relative_discomfort_ROUNDED"] = city_results["relative_discomfort"].round(2)
    city_results["relative_distance_ROUNDED"] = city_results["relative_distance"].round(2)
    city_results_length1 = city_results.shape[0]

    city_results = city_results.drop_duplicates(["relative_discomfort_ROUNDED", "relative_distance_ROUNDED"], keep = "first")
    city_results_length2 = city_results.shape[0]

    some_betas_were_skipped = city_results_length2 < city_results_length1

    domx = [max(city_results["relative_distance"].min() - 0.01, 1), city_results["relative_distance"].max() + 0.02]
    domy = [max(city_results["relative_discomfort"].min() - 0.01, 0), city_results["relative_discomfort"].max() + 0.01]

    base = alt.Chart(city_results).mark_line(
        point = False,
        color = "black",
    ).encode(
        x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
        y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
    )

    chart2 = alt.Chart(city_results).mark_point(
        filled = True,
        opacity = 1,
    ).encode(
        x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
        y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
        color = alt.Color("beta:N", title = "Beta (Discomfort Sensitivity)", scale = alt.Scale(scheme = "viridis")),
        tooltip = [
            alt.Tooltip("relative_distance:Q", title = "Relative Distance (Circuity)"),
            alt.Tooltip("relative_discomfort:Q", title = "Relative Discomfort"),
            alt.Tooltip("beta:N", title = "Beta (Discomfort Sensitivity)"),
            alt.Tooltip("tradeoff_rate:N", title = "Tradeoff Rate from this Beta"),
        ]
    )

    text = base.mark_text(
        fontSize = 15,
        dy = -25,
        dx = 10,
        angle = 335,
        align="left",
        baseline="middle",
        lineBreak=r"\n",
    ).encode(
        text = alt.Text("text_display:N"),
    )

    arrow = alt.Chart(city_results.iloc[1:]).mark_point(shape="arrow", filled=True, opacity = 1, color = "white", size = 300).encode(
        x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
        y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
        angle = alt.AngleValue(140)
    )
    
    chart = (base + text + chart2 + arrow).configure_point(
        size = 500
    ).properties(
        title = f"{mode_option} Curve for {place_name}",
        width=650,
        height=400
    )

    st.altair_chart(chart)

    st.caption("*MTOR: Modified Trade-off Rate. **Higher MTOR is better.**")

    if some_betas_were_skipped:
        st.caption(r"The full set of Beta values tested is {0, 0.5, 1, 1.5, 2, 2.5, 3}. If any of these values are not present in the chart above, it is because there was no change in relative discomfort or relative distance was measured, compared to lower values of Beta.")

    st.markdown("### Interpretation")
    st.markdown("Higher values of Beta indicate higher sensitivity to discomfort, i.e., cyclists/pedestrians who are willing to take longer detours to improve comfort.\n\nThe lowest value, 'Beta=0.0', is the case where a person is not sensitive to discomfort; they simply try to take the shortest possible path.")

    beta_pair_option = st.radio("Choose a Beta interval", options = city_results.index[1:], format_func = lambda x: tor_df.at[x, "beta_pair"], horizontal=True)

    row = city_results.loc[beta_pair_option]

    # with st.container(border=True):

    overall_colspec = [1.4, 0.8, 0.2, 0.8]
    colspec = overall_colspec[1:]
    maincolspec = [overall_colspec[0], sum(colspec)]

    maincol1, maincol2 = st.columns(maincolspec)

    with maincol1:
        with st.container(border = True):
            st.markdown(f"#### At Beta={row['beta']}, MTOR={row['tradeoff_rate_rounded']}.")

            interpretation = f'- To reduce discomfort by **{round(row["discomfort_change_percent"], 1)}%**, you need a detour that is **{round(row["distance_change_percent"], 1)}%** longer, vs. route taken with lower sensitivity to discomfort (Beta={row["lower_beta"]}).\n- Discomfort decreases **{row["tradeoff_rate_rounded"]} times** as much as the extra distance, percentagewise.'

            st.markdown(interpretation)

    with maincol2:

        with st.container(border = True):

            with st.container():

                col1, col2, col3 = st.columns(colspec)

                with col1:
                    st.metric(
                        f"Relative Discomfort",
                        round(row['relative_discomfort'], 3),
                        delta = f"-{round(row['discomfort_change_exact'], 3)} (by {round(row['discomfort_change_percent'], 1)}%)",
                        delta_color = "inverse"
                    )

                with col2:
                    st.markdown("# ←")

                with col3:

                    st.metric(
                        f"versus Beta={row['lower_beta']}:",
                        round(row['relative_discomfort_PREVIOUS'], 3),
                        delta = "",
                        delta_color = "off"
                    )

            with st.container():

                col1, col2, col3 = st.columns(colspec)

                with col1:

                    st.metric(
                            f"Relative Distance",
                            round(row['relative_distance'], 3),
                            delta = f"{round(row['distance_change_exact'], 3)} (by {round(row['distance_change_percent'], 1)}%)",
                            delta_color = "inverse"
                        )

                with col2:
                    st.markdown("# ←")

                with col3:

                    st.metric(
                        f"versus Beta={row['lower_beta']}:",
                        round(row['relative_distance_PREVIOUS'], 3),
                        delta = "",
                        delta_color = "off"
                    )
    
    display_explanation_expander()

    return None

def display_best_and_worst_by_average(brgy_metrics_filtered, brgy_results_filtered, metric, metric_str, lowest_is_best = True, note_relative_position_on_graph = True, topbottom = True, custom_captions = None):

    m_sorted = brgy_metrics_filtered.sort_values(metric, ascending = lowest_is_best)
    best_brgy_row = m_sorted.iloc[0]
    worst_brgy_row = m_sorted.iloc[-1]

    pos_list = ["bottom", "top"] if topbottom else ["left side", "right side"]
    if not lowest_is_best:
        pos_list = pos_list[::-1]

    symbol_list = ["↓", "↑"]
    if not lowest_is_best:
        symbol_list = symbol_list[::-1]

    col1, col2 = st.columns([1, 1])
    with col1:

        brgy_name = best_brgy_row['adm4_en']

        subcol1, subcol2 = st.columns([1, 1])
        with subcol1:
            st.markdown(f"<h5 style = 'color:green'> {brgy_name}</h5>", unsafe_allow_html=True)
            st.markdown(f"has the best average {metric_str}:")
        with subcol2:
            with st.container(border = True):
                symbol_best = symbol_list[0]
                st.markdown(
                    f"<h2 style = 'color:green'>{round(best_brgy_row[metric], 3)} {symbol_best}</h2>",
                    unsafe_allow_html=True
                )

        if custom_captions is not None:
            st.caption(custom_captions["best"])
        elif note_relative_position_on_graph:
            pos_best = pos_list[0]
            st.caption(f"(The curve for {brgy_name} is closest to the **{pos_best}** of the graph.)")

    with col2:

        brgy_name = worst_brgy_row['adm4_en']

        subcol1, subcol2 = st.columns([1, 1])
        with subcol1:
            st.markdown(f"<h5 style = 'color:red'> {brgy_name}</h5>", unsafe_allow_html=True)
            st.markdown(f"has the worst *average* {metric_str}:")
        with subcol2:
            symbol_worst = symbol_list[1]
            with st.container(border = True):
                st.markdown(
                    f"<h2 style = 'color:red'>{round(worst_brgy_row[metric], 3)} {symbol_worst}</h2>",
                    unsafe_allow_html=True
                )

        if custom_captions is not None:
            st.caption(custom_captions["worst"])
        elif note_relative_position_on_graph:
            pos_worst = pos_list[1]
            st.caption(f"(The curve for {brgy_name} is closest to the **{pos_worst}** of the graph.)")

    return None



#----------------------------------------------

# Main

if __name__ == "__main__":

    # DATA
    brgy_bike_results, brgy_walk_results, brgy_bike_metrics, brgy_walk_metrics, city_bike_results, city_walk_results, city_bike_metrics, city_walk_metrics = load_curve_data()

    # START
    st.markdown("# Bikeability and Walkability Curves")

    mode_option = st.radio(
        "Analysis",
        options = ["Bikeability", "Walkability"]
    )

    if mode_option == "Bikeability":
        brgy_results = brgy_bike_results
        brgy_metrics = brgy_bike_metrics
        city_results = city_bike_results
        city_metrics = city_bike_metrics

    elif mode_option == "Walkability":
        brgy_results = brgy_walk_results
        brgy_metrics = brgy_walk_metrics
        city_results = city_walk_results
        city_metrics = city_walk_metrics

    city_tab, brgy_tab = st.tabs(["City-wide", "Barangay-wide"])

    with city_tab:
                
        display_single_area_analysis(city_metrics, city_results, place_name = "City of Mandaluyong")
            
    with brgy_tab:

        # define presets here
        @st.cache_data(ttl = None, max_entries = 10)
        def get_dfs_for_top_k(brgy_metrics, brgy_results, metric, lowest = True, k = 5):
            m = brgy_metrics.sort_values(metric, ascending=lowest)
            m_top = m.iloc[:k]
            top_brgy_pcodes = m_top["adm4_pcode"].unique()
            r_top = brgy_results.loc[brgy_results["adm4_pcode"].isin(top_brgy_pcodes)]

            return top_brgy_pcodes, m_top, r_top
        
        @st.cache_data(ttl = None, max_entries = 10)
        def preset_best_brgys_overall(brgy_metrics, brgy_results, k = 5):
            m1 = brgy_metrics.sort_values("average_circuity", ascending=True).iloc[:15]
            m2 = brgy_metrics.sort_values("average_relative_discomfort", ascending=True).iloc[:15]
            m_top = m1.loc[m1["adm4_pcode"].isin(m2["adm4_pcode"])].sort_values("average_relative_discomfort", ascending = True)
            m_top = m_top.iloc[:k]
            top_brgy_pcodes = m_top["adm4_pcode"].unique()
            r_top = brgy_results.loc[brgy_results["adm4_pcode"].isin(top_brgy_pcodes)]

            return top_brgy_pcodes, m_top, r_top
        
        @st.cache_data(ttl = None, max_entries = 10)
        def preset_all_barangays(brgy_metrics, brgy_results):
            return (brgy_metrics["adm4_pcode"].unique(), brgy_metrics, brgy_results)
        
        chosen_k = 5

        preset_dict = {
            "Select barangays manually": None,
            "Use Preset: Best Barangays Overall": preset_best_brgys_overall(brgy_metrics, brgy_results),
            f"Use Preset: Best {chosen_k} Barangays by Lowest Circuity": get_dfs_for_top_k(brgy_metrics, brgy_results, "average_circuity", lowest = True),
            f"Use Preset: Best {chosen_k} Barangays by Lowest Relative Discomfort": get_dfs_for_top_k(brgy_metrics, brgy_results, "average_relative_discomfort", lowest = True),
            f"Use Preset: Worst {chosen_k} Barangays by Highest Circuity": get_dfs_for_top_k(brgy_metrics, brgy_results, "average_circuity", lowest = False),
            f"Use Preset: Worst {chosen_k} Barangays by Highest Relative Discomfort": get_dfs_for_top_k(brgy_metrics, brgy_results, "average_relative_discomfort", lowest = False),
            "Use Preset: All Barangays": preset_all_barangays(brgy_metrics, brgy_results),
        }

        ### ask to select preset
        preset_choice = st.selectbox(
            "Choose what you want to do:",
            options = preset_dict.keys(),
        )
        preset_result = preset_dict[preset_choice]

        if preset_result is None: # no preset selected
            brgys_filtered = st.multiselect(
                "Select barangays here:",
                options = brgy_metrics.index, # the p-codes
                default = ["PH137401022"], # plainview
                format_func = lambda x: brgy_metrics.at[x, "adm4_en"],
            )
            brgy_results_filtered = brgy_results.loc[brgy_results["adm4_pcode"].isin(brgys_filtered)]
            brgy_metrics_filtered = brgy_metrics.loc[brgys_filtered]

        else: # use preset
            brgys_filtered, brgy_metrics_filtered, brgy_results_filtered = preset_result
            if preset_choice == "Use Preset: Best Barangays Overall":
                st.info("**Best Barangays Overall:** This preset shows 5 barangays such that each barangay is both in the best 15 barangays with the lowest circuity and in the best 15 barangays with the lowest discomfort.")

        num_brgys_selected = len(brgys_filtered)

        if num_brgys_selected == 0:
            st.warning("Choose at least one barangay.")
            st.stop()

        else:
            st.divider()
        
            if num_brgys_selected == 1:
                brgy_name = brgy_metrics_filtered.iloc[0]["adm4_en"]
                display_single_area_analysis(brgy_metrics_filtered, brgy_results_filtered, place_name = brgy_name)

            else: # for comparing 2 or more barangays

                # Display curve chart

                df = brgy_results_filtered

                domx = [df["relative_distance"].min() - 0.1, df["relative_distance"].max() + 0.05]
                domy = [df["relative_discomfort"].min() - 0.01, df["relative_discomfort"].max() + 0.01]

                color_scale = alt.Scale(scheme = "dark2")

                base = alt.Chart(df).mark_line(
                    point = False
                ).encode(
                    x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
                    y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
                    color = alt.Color("adm4_en:N", title = "Barangay", legend = None, scale = color_scale),
                    tooltip = (
                        alt.Tooltip("adm4_en:N", title = "Barangay"),
                        alt.Tooltip("beta:O", title = "Beta"),
                        alt.Tooltip("relative_distance:Q", title = "Relative Distance (Circuity)"),
                        alt.Tooltip("relative_discomfort:Q", title = "Relative Discomfort"),
                    )
                )

                points = alt.Chart(df).mark_point(
                    filled = True,
                    opacity = 1,
                ).encode(
                    x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
                    y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
                    color = alt.Color("adm4_en:N", title = "Barangay", scale = color_scale),
                    shape = alt.Shape("adm4_en:N", title = "Barangay"),
                    tooltip = (
                        alt.Tooltip("adm4_en:N", title = "Barangay"),
                        alt.Tooltip("beta:O", title = "Beta"),
                        alt.Tooltip("relative_distance:Q", title = "Relative Distance (Circuity)"),
                        alt.Tooltip("relative_discomfort:Q", title = "Relative Discomfort"),
                    )
                )

                include_text = len(brgys_filtered) <= 10
                if include_text:
                    only_beta_zero = df.loc[df["beta"] == 0].merge(
                        brgy_metrics_filtered[["adm4_pcode", "average_tradeoff_rate", "average_circuity", "average_relative_discomfort"]],
                        left_on = "adm4_pcode",
                        right_index = True,
                        how = "inner"
                    )
                    text = alt.Chart(only_beta_zero).mark_text(
                        fontSize = 15,
                        align = "right",
                        dx = -30,
                        dy = -10,
                        clip = False
                    ).encode(
                        x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
                        y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
                        text = alt.Text("adm4_en:N", title = "Barangay"),
                        color = alt.Color("adm4_en:N", title = "Barangay", legend = None, scale = color_scale),
                        tooltip = (
                            alt.Tooltip("adm4_en:N", title = "Barangay"),
                            alt.Tooltip("average_circuity:Q", title = "Average Circuity"),
                            alt.Tooltip("average_relative_discomfort:Q", title = "Average Relative Discomfort"),
                        )
                    )
                    chart = base + text
                else:
                    chart = base

                chart = (
                    chart + points
                ).configure_point(
                    size = 150
                ).properties(
                    title = f"Comparison of Barangay {mode_option} Curves",
                    height = 450,
                    width = 650
                ).resolve_scale(
                    color = "independent",
                    shape = "independent"
                ).interactive()

                st.altair_chart(chart)

                st.info(f":heavy_exclamation_mark: A {mode_option} Curve is better if it is closer to the **bottom left** of the graph.")


                # Display interpretations
                st.markdown("## Interpretations")

                st.markdown("Among the *selected barangays only*, we can conclude the following.")

                with st.container(border = True):
                    st.markdown("### :sweat: Relative Discomfort")
                    st.caption("Lower is better.")
                    st.markdown("</br>", unsafe_allow_html=True)
                    
                    display_best_and_worst_by_average(
                        brgy_metrics_filtered,
                        brgy_results_filtered,
                        metric = "average_relative_discomfort",
                        metric_str = "relative discomfort",
                        lowest_is_best = True,
                        note_relative_position_on_graph = True,
                        topbottom = True
                    )

                with st.container(border = True):
                    st.markdown("### :straight_ruler: Relative Distance (Circuity)")
                    st.caption("Lower is better.")
                    st.markdown("</br>", unsafe_allow_html=True)
                    
                    display_best_and_worst_by_average(
                        brgy_metrics_filtered,
                        brgy_results_filtered,
                        metric = "average_circuity",
                        metric_str = "circuity",
                        lowest_is_best = True,
                        note_relative_position_on_graph = True,
                        topbottom = False
                    )
                with st.container(border = True):
                    st.markdown("### :arrows_clockwise: Modified Trade-off Rate (MTOR)")
                    st.caption("Higher is better.")
                    st.markdown("</br>", unsafe_allow_html=True)
                    
                    display_best_and_worst_by_average(
                        brgy_metrics_filtered,
                        brgy_results_filtered,
                        metric = "average_tradeoff_rate",
                        metric_str = "MTOR",
                        lowest_is_best = False,
                        note_relative_position_on_graph = False,
                        topbottom = False,
                        custom_captions = {
                            "best": "A higher value is better as it corresponds to a steeper line (more discomfort is reduced per increase in distance, percentagewise.)",
                            "worst": ""
                        }
                    )

                display_explanation_expander()