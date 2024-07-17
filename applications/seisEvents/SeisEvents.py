# Tektonik plakaların geojson
# https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json
import json
# import dash_leaflet.express as dlx
from dash import Dash,html,dcc,callback,Output,Input,State
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import arrow_function, assign
import plotly.graph_objects as go
from SeisEventsFunctions import GetUSGSEvents,USGS_EventsDataToDataFrame
import plotly.express as px

# External Style
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"

# Create colorbar func
# def Get_CategoricalColorbar(classes : list, colorscale : list, **kwargs):
#     ctg = ["{}+".format(cls,classes[i + 1]) for i,cls in enumerate(classes[:-1])] + ["{}+".format(classes[-1])]
#     colorbar = dlx.categorical_colorbar(categories=ctg,colorscale=colorscale,**kwargs)
#     return colorbar

# Get Info Data
def Get_Info(feature = None, headtext : str = ""):
    header = [html.H4(headtext)]
    if not feature:
        return header + [html.P("Hoover over a city/state")]
    return header + [html.B(feature["properties"]["name"]), html.Sup("2")]

# Create Info Control
info = html.Div(children=Get_Info(), id="info", className="info", style={"position" : "absolute", "top" : "10px", "right" : "10px", "zIndex" : "1000"})

# Javascript func 
on_each_feature = assign("""function(feature,layer,context){
                            layer.bindTooltip(`${feature.properties.ADMIN} ${feature.properties.density}`)
                        }
""")
# Get Latest Earthquake data whole world from USGS Web Service
latest_events = GetUSGSEvents()
df_events     = USGS_EventsDataToDataFrame(latest_events)
    
# Get geojson data
countries = json.load(open("assets\\countries.geojson",'r'))
# print(countries.keys())

# # Create Map
# fig = px.choropleth(df_events,geojson=countries['features'])
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

map = html.Div([
    dl.Map(
        [dl.TileLayer(),  # Varsayılan temel harita katmanı
         dl.GeoJSON(data=countries,  # GeoJSON verisi
                    cluster=True,
                     options={'style': {'color': 'blue'}}),  # İşaretçi rengi
         dl.Marker(position=[],  # İşaretçi koordinatları
                   children=dl.Tooltip("Merhaba!"))],  # İşaretçi üzerine gelindiğinde görünen metin
        style={'width': '100%', 'height': '80vh', 'margin': "auto", "display": "block"}
    )
])
# Create App
app = Dash(__name__,external_scripts=[chroma], prevent_initial_callbacks=True)
app.layout = [map]

# @callback(Output("info","children"), Input("geojson","hoverData"))
# def info_hover(feature):
#     return Get_Info(feature)

if __name__ == "__main__":
    app.run_server(debug=True)
    # print(earthquake_gdf['geometry'])
    # print(earthquake_gdf['geometry'][0])
    # print(countries['features'][0])