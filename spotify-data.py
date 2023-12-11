import json

import pandas as pd
import os
import numpy as np
import dash
from dash import Dash, dcc, html
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output

dfs = []

## <<-->> DO NOT CHANGE <<-->> ##

for filename in os.listdir(r"C:\Users\johnb\Desktop\ssspp"):
    if filename.endswith(".json"):
        df = pd.read_json(filename)
        dfs.append(df)
d = pd.concat(dfs, ignore_index=True)
d = d.drop(d[d['ms_played']<30000].index)
d = (d[d.episode_name.isnull()])
print(d)

## <<-->> DO NOT CHANGE <<-->> ##

## time filter.l.old = d[d['ts'] >= '2023-01-01']

d['ts'] = pd.to_datetime(d['ts']).dt.tz_convert('America/Los_Angeles')

m = (d['ms_played'].sum())

total_songs = len(d)

# Bar chart
unique_values_counts = d['master_metadata_album_artist_name'].value_counts().reset_index()
unique_values_counts.columns = ['Artist', 'Songs Played']
top_songs = d["master_metadata_track_name"].value_counts().reset_index()
top_songs.columns = ['Song Name', 'Times Played']
top_songs.sort_values('Times Played')

top_artists = unique_values_counts[:10]

# radial time chart
#filtered_data = d[d['master_metadata_album_artist_name'] == "Gorillaz"]

## radial chart ##
filtered_data = d
time_radial_data = filtered_data.groupby(pd.to_datetime(filtered_data.ts).dt.hour).ts
most_common_hour = pd.DataFrame({
    'hour': pd.to_datetime(filtered_data.ts).dt.hour.value_counts().sort_index().index,
    'Songs Played': pd.to_datetime(filtered_data.ts).dt.hour.value_counts().sort_index().values # ignore how goofy and  silly this code is
}).sort_values('hour').assign(Hour=lambda x: x['hour'] * 15)
## radial chart ##

# song over the year(s)

song_name = 'Hacker'

song_name_overtime = d[d["master_metadata_track_name"] == song_name]

times = pd.to_datetime(song_name_overtime.ts)

df = pd.DataFrame({'datetime': pd.to_datetime(times)})
df['month'] = df['datetime'].dt.month
df = df['month'].value_counts().reset_index()
df.columns = ['month','played']
df = df.sort_values('month')

## time of year (month) vs number of times listend to artist


hours = round((m / 1000 / 60 / 60))

# visit http://127.0.0.1:8050/ in your web browser.

app = Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#ADD8E6'
}

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

artistchart = px.bar(top_artists, x="Artist", y="Songs Played", barmode="group")

artistchart.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

top_song_graph = px.bar(top_songs[:10], y="Song Name", x="Times Played", orientation = "h")

top_song_graph.update_layout({
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']}})

timechart = px.bar_polar(most_common_hour, r="Songs Played", theta="Hour", template="plotly_dark",
                    color_discrete_sequence=px.colors.sequential.Plasma_r)
timechart.update_layout(
    title='Listening vs time of day',
    title_x = 0.5,
    font_size=16,
    legend_font_size=16,
    polar_radialaxis_ticksuffix='%',
    polar_angularaxis_rotation=90,

    polar=dict(

        radialaxis=dict(
            visible=False,
            tickmode='array',
            tickvals=[],
            ticktext=['0°', '90°', '180°', '279°'],
            angle=30
        ),
        angularaxis=dict(
            tickmode='array',
            tickvals=np.arange(0, 360, 15),  # Adjust as needed
            ticktext=[i for i in range(0, 24)],  # Adjust as needed
        )
    )

)


# app layout stuff

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[

    html.Div([ # dropdown
        dcc.Dropdown(['2020', '2021','2022, 2023'], id='demo-dropdown', style = {"justifyContent":"50%"}),
        html.Div(id='dd-output-container'),

    ]),

    html.H1( # page title
        children=f'Hours listened: {hours}',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    html.Div(children=f"Thats {round(hours/24, 1)} days!", style={ # sub title
        'textAlign': 'center',
        'color': colors['text']
    }),

    dcc.Graph( # top artist chart
        id='example-graph-2',
        figure=artistchart
    ),
    dcc.Graph( # radial time of day chart
        id='test',
        figure=timechart

    ),

    dcc.Graph( # top song graph
        id="top-song-graph",
        figure=top_song_graph
    ),
    html.Div([ # search bar
    dcc.Input(
        id="search", placeholder="Search", style = {'marginRight':'40px', "textAlign":'center', "jutifyContent":'center'}),
    html.Div(id="output")
    ]),


    dcc.Graph(id='search-test', style={"textAlign":"center"}),

])
@app.callback(
    Output('search-test', 'figure'),
    [Input('search', 'value')]
)
def update_scatter_plot(song_name):
    # Filter data based on the input species
    if song_name != 'all':

        filtered_df = d[d['master_metadata_track_name'] == song_name]
    else:
        filtered_df = d

    # Extract year-month from the timestamp
    filtered_df['year_month'] = filtered_df['ts'].dt.to_period('M')  # Convert to Period for year-month grouping

    Hours_played_of_song = (
        round(
            sum(
                filtered_df['ms_played'] / 1000 / 60 / 60
                    )
                ,2)
          )

    # Group by year-month and count occurrences
    monthly_counts = filtered_df.groupby('year_month').size().reset_index(name='count')
    monthly_counts['year_month'] = monthly_counts['year_month'].astype(str)


    fig = px.bar(
        monthly_counts,
        x='year_month',
        y='count',
        title=f'Song: {song_name}, {sum(monthly_counts["count"])} Plays Total, {Hours_played_of_song} hours played, avg time played (mins) {round((Hours_played_of_song*60)/max(sum(monthly_counts["count"]), .001),1)}',

    )

    fig.update_layout(xaxis_tickangle=90)
    fig.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y",
    )
    fig.update_layout({
        'plot_bgcolor': colors['background'],
        'paper_bgcolor': colors['background'],
        'font': {
            'color': colors['text']}})

    fig_json = fig.to_json()
    return json.loads(fig_json)

if __name__ == '__main__':
    app.run(debug=True)
