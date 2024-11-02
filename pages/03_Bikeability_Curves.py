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

    brgy_bike_metrics = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_bike_metrics.csv", index_col = "adm4_pcode")
    brgy_walk_metrics = pd.read_csv("migs_pages_data/brgy_curve_analysis/brgy_walk_metrics.csv", index_col = "adm4_pcode")

    city_bike_results = pd.read_csv("migs_pages_data/city_curve_analysis/city_bike_results.csv")
    city_walk_results = pd.read_csv("migs_pages_data/city_curve_analysis/city_walk_results.csv")

    city_bike_metrics = city_bike_results.drop("beta", axis = 1).mean(axis = 0)
    city_walk_metrics = city_walk_results.drop("beta", axis = 1).mean(axis = 0)

    return brgy_bike_results, brgy_walk_results, brgy_bike_metrics, brgy_walk_metrics, city_bike_results, city_walk_results, city_bike_metrics, city_walk_metrics

def tradeoff_rate(r1, r2):
    dist_change = 100 * ((r2["relative_distance"] / r1["relative_distance"]) - 1)
    discomfort_change = 100 * (1 - (r2["relative_discomfort"] / r1["relative_discomfort"]))
    if dist_change != 0:
        tor = abs( discomfort_change / dist_change )
    else:
        tor = np.nan
    return tor, dist_change, discomfort_change

def tradeoff_rates_from_results(results):
    new_rows = []
    results_df = results.sort_values("beta", ascending = True).reset_index(drop = True)
    max_index = results_df.shape[0] - 1

    for i, row1 in results_df.iterrows():
        if i+1 <= max_index:
            row2 = results_df.loc[i+1]
            beta_pair = f'Beta={row1["beta"]} to Beta={row2["beta"]}'
            tor, dist_change, discomfort_change = tradeoff_rate(row1, row2)
            rounded_tor = round(tor, 3)
            new_row = {
                "higher_beta": row2["beta"],
                "beta_pair": beta_pair,
                "tradeoff_rate": tor,
                "tradeoff_rate_rounded": rounded_tor,
                "distance_change": dist_change,
                "discomfort_change": discomfort_change,
                "text_display": fr"MTOR = {rounded_tor}", # modified TOR
                "interpretation": f"- To further decrease discomfort by {round(discomfort_change, 1)}%, one must take a detour that is {round(dist_change, 1)}% longer than before.\n- Discomfort decreases {round(tor, 1)} times, proportional to the extra distance. (TOR = {round(tor, 1)})."
            }
            new_rows.append(new_row)

    new_rows.append({
        "higher_beta": results_df.loc[0]["beta"],
        "tradeoff_rate": "not applicable",
        "text_display": "",
    })

    tor_df = pd.DataFrame(new_rows)
    return tor_df

#----------------------------------------------

# Main

if __name__ == "__main__":

    # SESSION STATE
    brgy_bike_results, brgy_walk_results, brgy_bike_metrics, brgy_walk_metrics, city_bike_results, city_walk_results, city_bike_metrics, city_walk_metrics = load_curve_data()

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

        tor_df = tradeoff_rates_from_results(city_results)

        city_results = city_results.merge(tor_df, left_on = "beta", right_on="higher_beta", how = "left")

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
            title = f"City {mode_option} Curve",
            width=650,
            height=400
        )

        st.altair_chart(chart)

        st.caption("*MTOR: Modified Trade-off Rate.")

        st.markdown("### Interpretation")
        st.markdown("Higher values of Beta indicate higher sensitivity to discomfort, meaning a person is more willing to take a detour to improve comfort. 'Beta=0.0' is the case where a person is not sensitive to discomfort; they try to take the shortest possible path.")

        beta_pair_option = st.radio("Choose a Beta interval", options = tor_df.index[:-1], format_func = lambda x: tor_df.at[x, "beta_pair"], horizontal=True)

        row = tor_df.loc[beta_pair_option]

        beta_pair = row["beta_pair"]
        interp = row["interpretation"]

        with st.container(border=True):

            st.markdown(f"Change from {beta_pair}: ")
            st.markdown(f"{interp}")
        
        with st.expander("Computations", expanded=False):
            st.markdown("""- Relative Distance (Circuity) is given by the distance of the best path, divided by the straight-line distance between the origin and destination.

- Relative Discomfort is given by the total discomfort of the best path, divided by the distance of that path. It can be interpreted as the rate at which discomfort is experienced for every meter travelled.
                        
- For different Beta values, the optimal path changes, so the Relative Distance and Relative Discomfort also change.
                                                
- MTOR (Modified Trade-off Rate) is given by the proportion decrease in relative discomfort, divided by the proportion increase in relative distance. This correlates with the slope of the graph. Higher MTOR (steeper slope) is better because it indicates that a relatively short detour can improve comfort greatly.""")
            
    with brgy_tab:
        brgy_multi = st.multiselect(
            "Select any number of barangays.",
            options = brgy_metrics.index,
            format_func = lambda x: brgy_metrics.at[x, "adm4_en"],
        )

        brgy_results_filtered = brgy_results.loc[brgy_results["adm4_pcode"].isin(brgy_multi)]
        brgy_metrics_filtered = brgy_metrics.loc[brgy_multi]

        brgy_metrics_filtered