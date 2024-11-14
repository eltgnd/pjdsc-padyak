# Packages
import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px

# Variables
ss = st.session_state
description = 'Lorem ipsum dolor sit amet.'
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
           "subcomponents": ("sidewalk", "FROM_IMAGES_sidewalk_ratio", "lit")


       },
       "safety_of_crossings": {
           "display_name": "Safety of Crossings",
           "description": "The weighted sum of data indicating whether specific roads have crosswalks, as well as the safety of specific crosswalks.",
           "subcomponents": ("TAG_crossing", "FROM_IMAGES_has_crosswalk")
       },
   }


# Callable

# Initialize
page_title = 'LGU Dashboard'
page_icon = '📊'
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="centered", initial_sidebar_state="auto", menu_items=None)


# Main
st.caption('PADYAK')
st.title('LGU Dashboard: Mandaluyong City')
st.write('\n')

# Import data
bike, walk = ss['bike'], ss['walk']

# Compute KPIs
def get_overall_metrics(df):
    return {
        'mean':df['score_weighted_by_sub'].mean()
    }

def get_component_metrics(df):
    mu_columns = [x for x in df.columns.tolist() if x[:3] == 'MU_']
    try:
        mu_columns.remove('MU_DISMOUNT')
    except ValueError:
        pass
    mu_formatted = [s[3:].replace('_', ' ').title() for s in mu_columns]

    scores = []
    for i in range(len(mu_columns)):
        scores.append(df[mu_columns[i]].mean())
    score_df = pd.DataFrame({
        'Component' : mu_formatted,
        'Score' : scores
    })
    
    mu_dict = {k:v for (k,v) in zip(mu_formatted, mu_columns)}

    return score_df, mu_dict

def get_road_metrics():
    df = walk
    sidewalk_status = {
        'Has Sidewalk' : df[df.sidewalk_description == 'has_sidewalk'].shape[0],
        'Is Sidewalk' : df[df.sidewalk_description == 'is_sidewalk'].shape[0],
        'No Sidewalk' : df[df.sidewalk_description == 'no_sidewalk'].shape[0]
    }
    bicycle_status = {
        'Bikeable' : df[df.bicycle_status == 'yes'].shape[0],
        'Not Bikeable' : df[df.bicycle_status == 'no'].shape[0],
        'Dismount' : df[df.bicycle_status == 'dismount'].shape[0],
        'Is Permissive' : df[df.bicycle_status == 'permissive'].shape[0]
    }
    crossing_status = {
        'Has Crossing' : df[df.is_crossing_status == True].shape[0],
        'No Crossing' : df[df.is_crossing_status == False].shape[0]
    }
    return sidewalk_status, bicycle_status, crossing_status

# Modularized parts

# Overall
def display_overall(df, title, emoji):
    st.caption(f'CITY-WIDE {title.upper()} METRICS')
    metrics = get_overall_metrics(df)

    col1, col2 = st.columns([0.3,0.7])
    with col1:
        with st.container(border=True):
            st.metric(f'Average {title} Score', f"{round(metrics['mean'],2)}/10", delta='Improving')
        with st.container(border=True):
            st.metric(f'Total Recorded Edges', df.shape[0], delta='Recently Updated')
        with st.container(border=True):
            st.metric(f'Last Update', '11/14/24')
    with col2:
        with st.container(border=True):
            fig = px.histogram(df, x="score_weighted_by_sub",
                height=350,
                nbins=30,
                title='Score Distribution',
                labels={'score_weighted_by_sub':f'{title} Score'},
            )
            fig.update_layout(margin=dict(l=30, r=30, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)


# Component Metrics
def display_components(df, title, emoji):
    st.caption(f'COMPONENTS')

    info = bike_main_component_name_to_display_info if title == 'Bikeability' else walk_main_component_name_to_display_info

    score_df, mu_dict = get_component_metrics(df)
    fig = px.line_polar(score_df, r='Score', theta='Component', 
        title='Score Breakdown',
        height=400,
        line_close=True)
    fig.update_polars(bgcolor='#FFFFFF', radialaxis=dict(visible=False))
    fig.update_traces(fill='toself')
    fig.update_layout(margin=dict(l=35, r=35, t=50, b=20))

    col1, col2 = st.columns([0.7,0.3])
    with col1:
        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        with st.container(border=True):
            st.caption('COMPONENT DESCRIPTION')
            selected_component = st.selectbox('Select a component', mu_dict.keys(), key=f'{title}_component_description')
            st.write(info[mu_dict[selected_component][3:]]['description'])

            st.caption('SUBCOMPONENTS')
        
        with st.container(border=True):
            st.caption('NOTE: To maintain readability of the radar chart, the DISMOUNT component was removed.')

# Sidewalk Metrics
def display_road_metrics(df, title, emoji):
    st.caption(f'ROAD STATUS')

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            sidewalk, bicycle, crossing = get_road_metrics()
            status_response = st.radio('Select a Road Feature', ['Sidewalk', 'Bicycle', 'Crossing'], key=f'{title}_road_metrics', horizontal=True)
    with col2:
        with st.container(border=True):
            st.caption('NOTE: These are estimations computed after data cleaning available OpenStreetMap data. Data may be improved.')

    if status_response == 'Sidewalk':
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]
            i = 0
            for items in sidewalk.items():
                cols[i].metric(f'{items[0]} Count', items[1], delta='123')
                i += 1
    
    if status_response == 'Bicycle':
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            cols = [col1, col2, col3, col4]
            i = 0
            for items in bicycle.items():
                cols[i].metric(f'{items[0]} Count', items[1])
                i += 1

    if status_response == 'Crossing':
        with st.container(border=True):
            col1, col2 = st.columns(2)
            cols = [col1, col2]
            i = 0
            for items in crossing.items():
                cols[i].metric(f'{items[0]} Count', items[1])
                i += 1

def display_trend(df, title, emoji):
    df = pd.read_csv(f'streamlit_preparation/synthetic_data.csv')
    fig = px.line(df, x='Date', y=title,
        title=f'{title} Trend',
        height=200,
    )
    fig.update_layout(margin=dict(l=35, r=35, t=50, b=10))

    fig.add_vrect(
        x0='2024-01-15', x1='2025-01-15',
        fillcolor="LightBlue", opacity=0.1, line_width=0,
        annotation_text="Intervention Period", annotation_position="top right"
    )
    with st.container(border=True):
        st.plotly_chart(fig)
        st.caption(f'NOTE: The {title.lower()} trend is fictitious and is only for demonstrating the project\'s potential.')

# Create tabs
bike_tab, walk_tab = st.tabs(['🚲 Bikeability', '🚶 Walkability'])
with bike_tab:
    display_overall(bike, 'Bikeability', '🚲')
    st.write('\n')

    display_trend(bike, 'Bikeability', '🚲')
    st.write('\n')

    display_components(bike, 'Bikeability', '🚲')
    st.write('\n')

    display_road_metrics(bike, 'Bikeability', '🚲')


with walk_tab:
    display_overall(walk, 'Walkability', '🚶')
    st.write('\n')

    display_trend(walk, 'Walkability', '🚶')
    st.write('\n')

    display_components(walk, 'Walkability', '🚶')
    st.write('\n')

    display_road_metrics(walk, 'Walkability', '🚶')