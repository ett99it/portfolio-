import pylab as pl
import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import numpy as np
import pydeck as pdk
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as pex
import plotly.graph_objects as pg

st.title("New York Motor Vehicle Collisions")
st.markdown("This application is streamlit dashboard that can be used to analyze motor vehicle collision in NYC")
st.markdown("This may take a while as the CSV file is 450MB")

DATA_URL = "Data-Visual/pages/Motor_Vehicle_Collisions.csv"


# @app.route("/").
@st.cache_data(persist=True)
def load_clean_data(rows):
    df = pd.read_csv(DATA_URL, nrows=rows, low_memory=False)
    # data.seek(0)
    df = df.drop(columns=['VEHICLE TYPE CODE 5', 'CONTRIBUTING FACTOR VEHICLE 5', 'VEHICLE TYPE CODE 4',
                          'CONTRIBUTING FACTOR VEHICLE 4', 'VEHICLE TYPE CODE 3', 'CONTRIBUTING FACTOR VEHICLE 3',
                          'OFF STREET NAME'])

    # also need to drop ['LOCATION']
    df.drop('LOCATION', axis=1, inplace=True)
    df.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    df = df.dropna()
    # datetime for ['CRASH DATE']
    df['CRASH DATE'] = pd.to_datetime(df['CRASH DATE'])

    #  df.time for ['CRASH TIME']
    df['CRASH TIME'] = pd.to_datetime(df['CRASH TIME'], format='%H:%M').dt.time

    # making 'CRASH HOUR'
    df['CRASH HOUR'] = df['CRASH TIME'].apply(lambda x: x.strftime('%H')).astype(int)
    df = pd.DataFrame(df)
    return df


data = load_clean_data(100000)
original_data = data

st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in NYC", 0, 19)
st.map(data.query("`NUMBER OF PERSONS INJURED` >= @injured_people")[['LATITUDE', 'LONGITUDE']].dropna(how="any"),
       zoom=5)

st.subheader("Road accidents by day of the week")
days = data['CRASH DATE'].dt.day_name().value_counts()
days = days.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
st.bar_chart(days)

st.subheader("Road accidents by time")
rd = data['CRASH DATE'].value_counts()
st.line_chart(rd)


@st.cache_data(persist=True)
def load_data(rows):
    dat = pd.read_csv(DATA_URL, nrows=rows, parse_dates=[['CRASH DATE', 'CRASH TIME']])
    # data.seek(0)
    dat.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    dat.rename(lowercase, axis='columns', inplace=True)
    dat.rename(columns={'crash date_crash time': 'date/time'}, inplace=True)
    return dat


dat = load_data(100000)
st.write(dat)
# visualize on 2D map
st.header("How many collisons occur during a given time of day?")
# hour = st.selectbox("Hour to look at",range(0,24),1)
hour = st.slider("Hour to look at", 0, 23)
# hour = st.sidebar.slider("Hour to look at",0,23)
dat = dat[dat['date/time'].dt.hour == hour]
# visualize 3D map
st.markdown("Vehicle collision between %i:00 and %i:00" % (hour, (hour + 1) % 24))
midpoint = (np.average(dat['latitude']), np.average(dat['longitude']))

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    # add a layer to visualize on 3d map
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=dat[['date/time', 'latitude', 'longitude']],
            get_position=['longitude', 'latitude'],
            radius=100,
            extruded=True,
            pickable=True,
            elevation_scale=4,
            elevation_range=[0, 1000],
        ),
    ],
))

# chart and histogram
st.subheader("Breakdown of collision by %i:00 and %i:00" % (hour, (hour + 1) % 24))
filtered = dat[
    (dat['date/time'].dt.hour >= hour) & (dat['date/time'].dt.hour < (hour + 1))
    ]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

# make a dropdown search
st.header("Top 5 dangerous streets affected by types")
select = st.selectbox("Affected by type of people", ['Pedestrians', 'Cyclists', 'Motorists'])

if select == 'Pedestrians':
    st.write(dat.query("`number of pedestrians injured` >= 1")[['on street name', 'number of pedestrians injured']].sort_values(
        by=['number of pedestrians injured'], ascending=False).dropna(how='any')[:5])
elif select == 'Cyclists':
    st.write(dat.query("`number of cyclist injured`>= 1")[['on street name', 'number of cyclist injured']].sort_values(
        by=['number of cyclist injured'], ascending=False).dropna(how='any')[:5])
elif select == 'Motorists':
    st.write(dat.query("`number of motorist injured` >= 1")[['on street name', 'number of motorist injured']].sort_values(
        by=['number of motorist injured'], ascending=False).dropna(how='any')[:5])

if st.checkbox("Show Raw Data", False):
    st.subheader("Raw Data")
    st.write(dat)
