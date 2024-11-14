import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd

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

    results_df["relative_discomfort_ROUNDED"] = results_df["relative_discomfort"].round(2)
    results_df["relative_distance_ROUNDED"] = results_df["relative_distance"].round(2)

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

def display_single_area_analysis(city_metrics, city_results, place_name, mode):

    tor_df = tradeoff_rates_from_results(city_results)

    city_results = city_results.merge(tor_df, left_on = "beta", right_on="higher_beta", how = "left")

    # if both relative discomfort and relative distance had a very small change, drop duplicates.
    city_results["relative_discomfort_ROUNDED"] = city_results["relative_discomfort"].round(3)
    city_results["relative_distance_ROUNDED"] = city_results["relative_distance"].round(3)
    city_results_length1 = city_results.shape[0]

    city_results = city_results.sort_values("beta", ascending = True).drop_duplicates(["relative_discomfort_ROUNDED", "relative_distance_ROUNDED"], keep = "first")
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
            alt.Tooltip("tradeoff_rate:N", title = "MTOR from previous Beta"),
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
        tooltip=False
    ).encode(
        text = alt.Text("text_display:N"),
    )

    arrow = alt.Chart(city_results.iloc[1:]).mark_point(shape="arrow", filled=True, opacity = 1, color = "white", size = 300).encode(
        x = alt.X("relative_distance:Q", title = "Relative Distance (Circuity)", scale = alt.Scale(domain = domx)),
        y = alt.Y("relative_discomfort:Q", title = "Relative Discomfort", scale = alt.Scale(domain = domy)),
        angle = alt.AngleValue(135),
        tooltip = [
            alt.Tooltip("relative_distance:Q", title = "Relative Distance (Circuity)"),
            alt.Tooltip("relative_discomfort:Q", title = "Relative Discomfort"),
            alt.Tooltip("beta:N", title = "Beta (Discomfort Sensitivity)"),
            alt.Tooltip("tradeoff_rate:N", title = "MTOR from previous Beta"),
        ]
    )
    
    chart = (base + text + chart2 + arrow).configure_point(
        size = 500
    ).properties(
        title = f"{mode} Curve for {place_name}",
        width=650,
        height=450
    )

    st.altair_chart(chart)

    st.caption("*MTOR: Modified Trade-off Rate. **Higher MTOR is better.**")

    if some_betas_were_skipped:
        st.caption(r"The full set of Beta values tested is {0, 0.5, 1, 1.5, 2, 2.5, 3}. If any of these values are not present in the chart above, it is because there was no change in relative discomfort or relative distance was measured, compared to the next higher values of Beta.")

    if city_results.shape[0] <= 1:

        st.info("Since the relative distance and discomfort is the same for every Beta, in the case of this barangay, no Modified Trade-off Rate (MTOR) can be calculated.")

    else:

        st.markdown("### Interpretation")
        st.markdown("Higher values of Beta indicate higher sensitivity to discomfort, i.e., cyclists/pedestrians who are willing to take longer detours to improve comfort.\n\nThe lowest value, 'Beta=0.0', is the case where a person is not sensitive to discomfort; they simply try to take the shortest possible path.")

        beta_pair_option = st.radio("Choose a Beta interval", options = city_results.index[1:], format_func = lambda x: tor_df.at[x, "beta_pair"], horizontal=True)

        row = city_results.loc[beta_pair_option]

        overall_colspec = [1.2, 0.8, 0.2, 0.8]
        colspec = overall_colspec[1:]
        maincolspec = [overall_colspec[0], sum(colspec)]

        maincol1, maincol2 = st.columns(maincolspec)

        with maincol1:
            with st.container(border = True):
                st.markdown(f"#### At Beta={row['beta']}, MTOR={row['tradeoff_rate_rounded']}.")

                interpretation = f'- To reduce discomfort by **{round(row["discomfort_change_percent"], 2)}%**, you need a detour that is **{round(row["distance_change_percent"], 2)}%** longer, vs. the route taken with lower sensitivity to discomfort (Beta={row["lower_beta"]}).\n- Discomfort decreases **{row["tradeoff_rate_rounded"]} times** as much as the extra distance, percentagewise.'

                st.markdown(interpretation)

        with maincol2:

            with st.container(border = True):

                with st.container():

                    col1, col2, col3 = st.columns(colspec)

                    with col1:
                        st.metric(
                            f"Discomfort, Beta={row['higher_beta']}",
                            round(row['relative_discomfort'], 3),
                            delta = f"-{round(row['discomfort_change_exact'], 4)} (by {round(row['discomfort_change_percent'], 2)}%)",
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
                                f"Distance, Beta={row['higher_beta']}",
                                round(row['relative_distance'], 3),
                                delta = f"{round(row['distance_change_exact'], 4)} (by {round(row['distance_change_percent'], 2)}%)",
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