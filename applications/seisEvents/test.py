from pandas import DataFrame
from SeisEventsFunctions import USGS_EventsDataToDataFrame,GetUSGSEvents
import dash
from dash import dcc,html,Input, Output
from dash.dependencies import Input, Output
import dash_leaflet as dl
import json
from dash_extensions.javascript import arrow_function, assign
from dash_leaflet import express as dlx #protobuf exception -> https://stackoverflow.com/questions/72441758/typeerror-descriptors-cannot-not-be-created-directly ; solution -> pip install protobuf==3.20.*

# helpfull links
# https://medium.com/@mdavid800/plotly-dash-interactive-mapping-dash-leaflet-titiler-e0c362d15e4
# https://medium.com/mcd-unison/nested-maps-with-dash-leaflet-22cc6497481c
# https://stackoverflow.com/questions/75852166/add-popup-in-dl-geojson-dash-leaflet-python-dash
# https://community.plotly.com/t/show-and-tell-dash-leaflet/34924/385

# External Style
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
# main_js = "C:\\Users\\muham\\Masaüstü\\github\\seiskit-apps\\assets\\mainExtensions.js"

# Colorbar control for earthquake events locations
# =======================================================================================================
classes=[0,3,10,20,30,40,50]
colorscale=['blue','green','yellow','orange','brown', 'purple','red']
style     = dict(weight=2, opacity=1, color='black', dashArray='3', fillOpacity=0.7)
vmin = 0
vmax = 10
colorBars = dl.Colorbar(position="bottomright",colorscale="Viridis",style=style,min=vmin, max=vmax, unit='/km')

# Get Info Data
# =======================================================================================================
def Get_Info(feature = None, headtext : str = ""):
    header = [html.H4(headtext)]
    if not feature:
        return header + [html.P("Hoover over a country/city")]
    return header + [html.B(feature["properties"]["ADMIN"]),html.Br()] 

# Create Info Control
# =======================================================================================================
info = html.Div(children=Get_Info(), id="info", className="info", style={"position" : "absolute", "top" : "430px", "left" : "10px", "zIndex" : "1000"})



# Load GeoJSON datas
# =======================================================================================================
with open('applications\\seisEvents\\data\\tectonic_plates.json') as f:
    geojson_data = json.load(f)

with open('applications\\seisEvents\\data\\countries.geojson') as f:
    county_goejson_data = json.load(f)

with open('applications\\seisEvents\\data\\mtadirifay_2012.geojson') as f:
    mta_dirifay = json.load(f)

# Create GeoJSON objects.
# =======================================================================================================
techtonicPlates = dl.GeoJSON(data=geojson_data,
                             options=dict(style=dict(weight=1.2, color = "blue", pixelsize=1, fillOpacity=0.5)))

countries = dl.GeoJSON(data=county_goejson_data,
                    #    options=dict(onEachFeature = on_each_feature),
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    zoomToBoundsOnClick=True,  # when true, zooms to bounds when data changes
                    # pointToLayer=point_to_layer,  # how to draw points
                    # onEachFeature=on_each_feature,  # add (custom) tooltip
                    hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')), #style applied on hover
                    hideout=dict(colorProp='depth', 
                                 circleOptions=dict(fillOpacity=1, stroke=False, radius=5), 
                                 min=vmin, max=vmax, colorscale=colorscale),
                    id='county'
                    )

trFaults = dl.GeoJSON(data=mta_dirifay,
                      options=dict(style=dict(weight=1, color = "gray", pixelsize=1, fillOpacity=0.5)))

# EARTHQUAKE DATA 
# =======================================================================================================
usgsData = GetUSGSEvents()
df_usgs  = USGS_EventsDataToDataFrame(usgsData)

# on_each_feature_events = assign("""function(features, layer, context){
#     layer.bindTooltip(`${features.properties.place} (${features.properties.mag})`)
# }""")

#  This function determines the radius of the earthquake marker based on its magnitude.
#  Earthquakes with a magnitude of 0 were being plotted with the wrong radius.
# get_radius = assign("""
#   function getRadius(magnitude) {
#     if (magnitude === 0) {
#       return 1;
#     }
#     return magnitude * 4;
#   }
# """)

# point_to_layer_events = assign("""function(feature, latlng, context){
#     const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
#     const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
#     circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop
#     return L.circleMarker(latlng, circleOptions);  // render a simple circle marker
# }""")

# handle_style = assign("""function(feature, context){
#         const {classes, colorscale, style, colorProp} = context.props.hideout;  // get props from hideout
#         const value = feature.properties[colorProp];  // get value the determines the color
#         for (let i = 0; i < classes.length; ++i) {
#             if (value > classes[i]) {
#                 style.fillColor = colorscale[i];  // set the fill color according to the class
#             }
#         }
#         return style;
#     }""")

# geojson options ["pointToLayer", "style", "onEachFeature", "filter", "coordsToLatLng"]
# from dash_extensions.javascript import Namespace
# ns = Namespace("dashExtensions","default")
# events = dl.GeoJSON(
#                     data=usgsData,
#                     format="geojson",
#                     # options= dict( onEachFeature = ns('OnEachFutureEvents')),
#                     zoomToBounds=True,  # when true, zooms to bounds when data changes    
#                     zoomToBoundsOnClick=True,              
#                     id='EventsUSGS')

# Initialize Dash app
# =======================================================================================================
app = dash.Dash(__name__,external_scripts=[chroma], prevent_initial_callbacks=True,assets_url_path="C:\\Users\\muham\\Masaüstü\\github\\seiskit-apps\\applications\\seisEvents\\data")

# Create Layout
# =======================================================================================================
layersControl = dl.LayersControl([
                                    # BaseMap gösterim layer ı
                                    dl.Overlay(
                                        dl.LayerGroup(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}.png",id="TileMap")
                                        ),
                                        name="BaseMap",
                                        checked=True
                                        ),

                                    # Tektonik geojson gösterim layer ı
                                    dl.Overlay(
                                        dl.LayerGroup(techtonicPlates,id="TechtonicPlt"),
                                        name="TecthonicPlates",
                                        checked=False
                                        ),
                                    # Tr diri fay hattı gösterim layer ı
                                    dl.Overlay(
                                        dl.LayerGroup(trFaults,id="TrFlts"),
                                        name="TrFaults",
                                        checked=False
                                        ),

                                    dl.Overlay(
                                        dl.LayerGroup(id="earthquakes",children=[colorBars]),
                                        name="Events",
                                        checked=True
                                        ),

                                    #COG fed into Tilelayer using TiTiler url (taken from r["tiles"][0])
                                    # dl.Overlay(dl.LayerGroup(dl.TileLayer(url=r["tiles"][0], opacity=0.8,id="WindSpeed@100m")),name="WS@100m",checked=True),
                                    
                                    dl.LayerGroup(id="layer"),

                                    # set colorbar and location in app            
                                    # dl.Colorbar(colorscale=['blue','green','yellow','orange','brown', 'purple','red'], width=20, height=150, min=0, max=7,unit='m/s',position="bottomright"),
                                    # # info,
                                ])

map_Div = html.Div([
        html.H1(children='REAL-TIME EARTHQUAKE EVENTS MAP'),
        html.Div(
                    [
                        dl.Map( id='map',
                            center=[0,0],
                                zoomControl=True,
                                doubleClickZoom=True,
                                dragging=True,
                                scrollWheelZoom=True,
                                style={'width': '1000px', 'height': '500px'},
                                children=[  dl.TileLayer(),
                                            # countries,
                                            layersControl,
                                            # info
                                        ],
                                )
                    ],
                    
                    id='map_div', 
                    className='map_div'
                )],
        className='main_div')

container_map = html.Div([map_Div],className='container')

app.layout = [container_map]

# Callback functions
# =======================================================================================================
# @app.callback(Output("info","children"), Input("county","hover_feature"))
# def info_hover(feature):
#     return Get_Info(feature,headtext="Country")


@app.callback(Output("earthquakes", "children"), Input("map", "center") )
def update_map(_):
    # Process earthquake data and create markers
    # Load Earthquake data
    usgsData = GetUSGSEvents()
    df_usgs  = USGS_EventsDataToDataFrame(usgsData)
    # Example: Parse GeoJSON data and create dl.Marker components
    # ...
    markers = []
    # df_usgs.iloc()[index]["Lat [°]"], df_usgs.iloc()[index]["Lon [°]"]
    for index in range(0,df_usgs.last_valid_index()):
        sample_marker = dl.CircleMarker(center=[df_usgs.iloc()[index]["Lat"],
                                                df_usgs.iloc()[index]["Lon"]
                                                ], 
                                        children=[dl.Popup([html.B("Place :{}".format(df_usgs.iloc()[index]["place"])), html.Br()] + 
                                                           ["Magnitude : {}-{}".format(df_usgs.iloc()[index]["mag"],df_usgs.iloc()[index]["magnitude_type"])]
                                                          )
                                                ],
                                        radius= df_usgs.iloc()[index]['mag']*2,
                                        
        )
        markers.append(sample_marker)
    # Return the markers to be displayed on the map
    return markers  # List of dl.Marker components

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)