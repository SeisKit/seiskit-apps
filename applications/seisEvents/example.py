# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# import dash_leaflet as dl
# import pandas as pd

# # Sample earthquake data (replace with your actual data)
# earthquake_data = pd.DataFrame({
#     'latitude': [34.0522, 36.7783, 40.7128],  # Example latitudes
#     'longitude': [-118.2437, -119.4179, -74.0060],  # Example longitudes
#     'magnitude': [5.0, 6.2, 4.5]  # Example magnitudes
# })

# app = dash.Dash(__name__)

# app.layout = html.Div([
#     dl.Map(dl.TileLayer(), style={'height': '50vh'}, center=[36, -100], zoom=4),
#     dl.LayerGroup([
#         dl.CircleMarker(
#             center=(row['latitude'], row['longitude']),
#             radius=row['magnitude'] * 2,  # Adjust the scaling factor as needed
#             children=[f"Magnitude: {row['magnitude']:.1f}"]
#         )
#         for _, row in earthquake_data.iterrows()
#     ])
# ])

# if __name__ == '__main__':
#     app.run_server(debug=True)

import functools
import os

from SeisEventsFunctions import GetUSGSEvents, USGS_EventsDataToDataFrame
import chart_studio
import dash
import pandas as pd
import plotly.graph_objs as go
import requests
from dash import dcc, html
from dash.dependencies import Input, Output

# from dotenv import load_dotenv
from flask import Flask, json

DEBUG = True if os.environ.get("DEBUG") else False
# dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
# load_dotenv(dotenv_path)



usgs = "http://earthquake.usgs.gov/earthquakes/"
geoJsonFeed = "feed/v1.0/summary/4.5_month.geojson"
url = "{}{}".format(usgs, geoJsonFeed)
req = requests.get(url)
data = json.loads(req.text)

# local development
# with open('4.5_month.geojson') as data_file:
#     data = json.load(data_file)


# http://colorbrewer2.org/#type=sequential&scheme=YlOrRd&n=5
colorscale_magnitude = [
    [0, "#ffffb2"],
    [0.25, "#fecc5c"],
    [0.5, "#fd8d3c"],
    [0.75, "#f03b20"],
    [1, "#bd0026"],
]

# http://colorbrewer2.org/#type=sequential&scheme=Greys&n=3
colorscale_depth = [
    [0, "rgb(240,240,240)"],
    [0.5, "rgb(189,189,189)"],
    [1, "rgb(99,99,99)"],
]

theme = {
    "fontFamily": "Raleway",
    "backgroundColor": "#787878",
}


def create_td(series, col):
    val = series[col]
    if col == "Detail":
        td = html.Td(html.A(children="GeoJSON", href="{}".format(val), target="_blank"))
    else:
        td = html.Td(val)
    return td


def create_table(df):
    columns = ["Magnitude", "Latitude", "Longitude", "Time", "Place", "Detail"]
    num_rows = data["metadata"]["count"]
    thead = html.Thead(html.Tr([html.Th(col) for col in columns]))
    table_rows = list()
    for i in range(num_rows):
        tr = html.Tr(
            children=list(map(functools.partial(create_td, df.iloc[i]), columns))
        )
        table_rows.append(tr)
    tbody = html.Tbody(children=table_rows)
    table = html.Table(children=[thead, tbody], id="my-table")
    return table


def create_header(some_string):
    header_style = {
        "backgroundColor": theme["backgroundColor"],
        "padding": "1.5rem",
    }
    header = html.Header(html.H1(children=some_string, style=header_style))
    return header



def create_dropdowns():
    drop1 = dcc.Dropdown(
        options=[
            {"label": "Light", "value": "light"},
            {"label": "Dark", "value": "dark"},
            {"label": "Satellite", "value": "satellite"},
            {
                "label": "Custom",
                "value": "mapbox://styles/jackdbd/cj6nva4oi14542rqr3djx1liz",
            },
        ],
        value="dark",
        id="dropdown-map-style",
        className="three columns offset-by-one",
    )
    drop2 = dcc.Dropdown(
        options=[
            {"label": "World", "value": "world"},
            {"label": "Europe", "value": "europe"},
            {"label": "North America", "value": "north_america"},
            {"label": "South America", "value": "south_america"},
            {"label": "Africa", "value": "africa"},
            {"label": "Asia", "value": "asia"},
            {"label": "Oceania", "value": "oceania"},
        ],
        value="world",
        id="dropdown-region",
        className="three columns offset-by-four",
    )
    return [drop1, drop2]


def create_description():
    div = html.Div(
        children=[
            dcc.Markdown(
                """
            The redder the outer circle, the higher the magnitude. The darker 
            the inner circle, the deeper the earthquake.
                        
            > Currently no organization or government or scientist is capable 
            > of succesfully predicting the time and occurrence of an
            > earthquake.
            > — Michael Blanpied
            
            Use the table below to know more about the {} earthquakes that 
            exceeded magnitude 4.5 last month.

            ***
            """.format(
                    data["metadata"]["count"]
                ).replace(
                    "  ", ""
                )
            ),
        ],
    )
    return div


def create_content():
    # create empty figure. It will be updated when _update_graph is triggered
    graph = dcc.Graph(id="graph-geo")
    content = html.Div(graph, id="content")
    return content

usgsData = GetUSGSEvents()
df_usgs  = USGS_EventsDataToDataFrame(usgsData)

regions = {
    "world": {"lat": 0, "lon": 0, "zoom": 1},
    "europe": {"lat": 50, "lon": 0, "zoom": 3},
    "north_america": {"lat": 40, "lon": -100, "zoom": 2},
    "south_america": {"lat": -15, "lon": -60, "zoom": 2},
    "africa": {"lat": 0, "lon": 20, "zoom": 2},
    "asia": {"lat": 30, "lon": 100, "zoom": 2},
    "oceania": {"lat": -10, "lon": 130, "zoom": 2},
}

app_name = "Dash Earthquakes"
server = Flask(app_name)
server.secret_key = os.environ.get("SECRET_KEY", "default-secret-key")
app = dash.Dash(name=app_name, server=server)

app.layout = html.Div(
    children=[
        create_header(app_name),
        html.Div(
            children=[
                html.Div(create_dropdowns(), className="row"),
                html.Div(create_content(), className="row"),
                html.Div(create_description(), className="row"),
            ],
        ),
        # html.Hr(),
    ],
    className="container",
    style={"fontFamily": theme["fontFamily"]},
)


@app.callback(
    output=Output("graph-geo", "figure"),
    inputs=[Input("dropdown-map-style", "value"), Input("dropdown-region", "value")],
)
def _update_graph(map_style, region):
    dff = df_usgs
    radius_multiplier = {"inner": 1.5, "outer": 3}

    layout = go.Layout(
        autosize=True,
        hovermode="closest",
        height=750,
        font=dict(family=theme["fontFamily"]),
        margin=go.layout.Margin(l=0, r=0, t=45, b=10),
        mapbox=dict(
            bearing=0,
            center=dict(
                lat=regions[region]["lat"],
                lon=regions[region]["lon"],
            ),
            pitch=0,
            zoom=regions[region]["zoom"],
            style=map_style,
        ),
    )

    # outer circles represent magnitude
    # inner circles represent depth
    data = (
        go.Scattermapbox(
            lat=dff["Lat [°]"],
            lon=dff["Lon [°]"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                color=dff["mag"],
                colorscale=colorscale_magnitude,
                opacity=1,
                # showscale=True,
                size=dff["mag"] * radius_multiplier["outer"],
            ),
            text=dff["Text"],
            # hoverinfo='text',
            showlegend=False,
        ),
        go.Scattermapbox(
            lat=dff["Lat [°]"],
            lon=dff["Lon [°]"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                color=dff["depth [km]"],
                colorscale=colorscale_depth,
                opacity=1,
                # showscale=True,
                size=dff["mag"] * radius_multiplier["inner"],
            ),
            # hovering behavior is already handled by outer circles
            hoverinfo="skip",
            showlegend=False,
        ),
    )

    figure = go.Figure(data=data, layout=layout)
    return figure


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run_server(debug=True)
