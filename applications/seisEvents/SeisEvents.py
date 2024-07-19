import os
from pandas import DataFrame
from SeisEventsFunctions import DepthFilter, MagnitudeFilter, USGS_EventsDataToDataFrame,GetUSGSEvents
import dash_bootstrap_components as dbc
from dash import dcc,html,Input, Output,Dash
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
# https://dash.plotly.com/external-resources
# https://github.com/emilhe/dash-leaflet/issues/243

# External Style
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
# main_js = "C:\\Users\\muham\\Masaüstü\\github\\seiskit-apps\\assets\\mainExtensions.js"

# Colorbar control for earthquake events locations
# =======================================================================================================
classes=[0,3,10,20,30,40,50]
# Picnic , Jet , ylorrd "Viridis"

colorscale="ylorrd"
style     = dict(weight=2, opacity=0.5, color='black', dashArray='3')
vmin = 0
vmax = 50
colorBars = dl.Colorbar(position="bottomright",colorscale=colorscale,style=style,min=vmin, max=vmax, unit='/km')
# Create colorbar.
ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+".format(classes[-1])]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=300, height=10, position="bottomright")


# Get Info Data
# =======================================================================================================
def Get_Info(feature = None, headtext : str = ""):
    header = [html.Header(headtext)]
    if not feature:
        return header + [html.P("Hoover over a country/city")]
    return header + [html.P(feature["properties"]["ADMIN"]),html.Br()] 

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
                    #    options=dict(onEachFeature = on_each_feature,pointToLayer=point_to_layer),
                    options=dict(style = dict(color = "#D9D9D9")),
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    zoomToBoundsOnClick=True,  # when true, zooms to bounds when data changes
                    hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')), #style applied on hover
                    id='county',
                    )

trFaults = dl.GeoJSON(data=mta_dirifay,
                      options=dict(style=dict(weight=1, color = "gray", pixelsize=1, fillOpacity=0.5)))

# EARTHQUAKE DATA 
# =======================================================================================================
# usgsData = GetUSGSEvents()
# df_usgs  = USGS_EventsDataToDataFrame(usgsData)
Mag = MagnitudeFilter(MinMag=0.,MaxMag=10.)
Depth = DepthFilter(MinDepth=0., MaxDepth=5000.)
usgs_geojson = GetUSGSEvents()
df_usgs      = USGS_EventsDataToDataFrame(usgs_geojson)

# zoombounds = assign(""""function(features, layer, context,event){
#                                                                 features.on("click", function (event) {
#                                                                                                         // Assuming the clicked feature is a shape, not a point marker.
#                                                                                                         map.fitBounds(event.layer.getBounds());
#                                                                                                     });
#                                                                 }
#                     """)

on_each_feature_events = assign("""function(features, layer, context){
                                                                    layer.bindPopup(`
                                                                                        <div id='MarkerPopup' class="container" style:"flex-row align-center">
                                                                                            <div class:"col align-center">
                                                                                                <h2 style="margin: 0; margin-right: .5rem; font-size: large; color: red;"> 
                                                                                                            <span style="margin: 0; font-size: small;"> ${features.properties.magType} <span/>
                                                                                                            ${features.properties.mag}
                                                                                                </h2>
                                                                                            </div>
                                                                                            
                                                                                            
                                                                                            <div class='class="col align-center"'>

                                                                                                    <h4 margin=0. margin-bottom=.5rem>Place :${features.properties.place}</h4>
                                                                                                                                                                                                    
                                                                                                    <h4 style="margin:0.">Latidude :${features.geometry.coordinates[0]} Longitude : ${features.geometry.coordinates[1]}</h4>
                                                                                                    
                                                                                                    <h4 style="margin:0.">Depth : ${features.geometry.coordinates[2]}-km</h4>                     
                                                                                                    
                                                                                                    <a href="${features.properties.url}" target=_blank style="margin:0."> Details </a>
                                                                                                
                                                                                             </div>
                                                                                        </div>
                                                                                    `)
                                                                    }
                                """)


# how to draw points
point_to_layer_events = assign("""function(feature, latlng, context){
    const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
    circleOptions.fillColor = csc(feature.geometry.coordinates[colorProp]);  // set color based on color prop
    circleOptions.radius    = feature.properties.mag * 2;  // set color based on color prop
    circleOptions.fillOpacity = 0.;
    return new L.circleMarker(latlng,circleOptions);  // render a simple circle marker
}""")


# handle_style = assign("""function(feature, context){
#         const {classes, colorscale, style,  colorProp} = context.props.hideout;  // get props from hideout
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
events = dl.GeoJSON(data=usgs_geojson,
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    zoomToBoundsOnClick=True, # when true, zooms to bounds of feature (e.g. cluster) on click
                    options=dict(pointToLayer = point_to_layer_events,
                                 onEachFeature=on_each_feature_events,
                                 interactive = True),
                    id='EventsUSGS',
                    hideout=dict(colorProp=2,
                                 circleOptions=dict(stroke=True, weight = 1),
                                 min=vmin, 
                                 max=vmax, 
                                 colorscale=colorscale)
                    )

# Initialize Dash app
# =======================================================================================================
app = Dash(__name__,
           external_scripts=[chroma], 
           prevent_initial_callbacks=True,
           assets_folder=f"{os.getcwd()}/assets"
           )

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
                                    
                                    # Ülke sınırlarının geojson gösterim layer ı
                                    dl.Overlay(
                                        dl.LayerGroup([countries,info],id="Countries"),
                                        name="CountryBorders",
                                        checked=False
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

                                    # dl.Overlay(
                                    #     dl.LayerGroup(events,id="earthquakes"),
                                    #     name="Events",
                                    #     checked=True
                                    #     ),

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
                                           center = [0,0],
                                           zoom = 4,
                                           doubleClickZoom=True,
                                           dragging=True,
                                           style={'width': '100%', 'height': '500px', 'margin': "auto"},
                                           children=[  dl.TileLayer(),
                                                        dl.FullscreenControl(),
                                                        dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",activeColor="#214097", completedColor="#972158"),
                                                        dl.LayerGroup(events),
                                                        colorbar,
                                                        layersControl,
                                                        
                                                    ],
                                            )
                                    
                                ],
                                
                                id='map_div', 
                                className='map_div'
                            )
                ],
        className='main_div')

container_map = html.Div([map_Div],className='container')

app.layout = container_map

# Callback functions
# =======================================================================================================
@app.callback(Output("info","children"), Input("county","hover_feature"))
def info_hover(feature):
    return Get_Info(feature,headtext="Country")

def create_MarkerPopup(df : DataFrame, index : int) -> html:
    popup = dl.Popup([
                        html.B("Place :{}".format(df.iloc()[index]["place"])), 
                        html.Br(),
                        html.B("Latidude :{} Longitude : {}".format(df.iloc()[index]["Lat"],df.iloc()[index]["Lon"])), 
                        html.Br(),
                        html.B("Magnitude : {}-{}".format(df.iloc()[index]["mag"],df.iloc()[index]["magnitude_type"])), 
                        html.Br(),
                        html.B("Depth : {}-km".format(df.iloc()[index]["depth"])), 
                        html.Br(),
                        html.Div( children=[html.A('Details' , href=df.iloc()[index]["url"], target="_blank")] )
                       ]                                                           
                    )
    return popup



# @app.callback(Output("earthquakes", "children"), Input("map", "center") )
# def update_map(_):
#     # Process earthquake data and create markers
#     # Load Earthquake data
#     usgsData = GetUSGSEvents()
#     df_usgs  = USGS_EventsDataToDataFrame(usgsData)
#     # Example: Parse GeoJSON data and create dl.Marker components
#     # ...
#     markers = [  dl.CircleMarker(id       = str(index),
#                                  weight   = 2,
#                                  stroke   = True,
#                                  center   = [df_usgs.iloc()[index]["Lat"],df_usgs.iloc()[index]["Lon"]], 
#                                  children = [create_MarkerPopup(df_usgs,index)],
#                                  radius   = df_usgs.iloc()[index]['mag']*4,
#                                  color    = str(df_usgs.iloc()[index]['depth'])
#                                         ) for index in range(0,df_usgs.last_valid_index())

#                ]
    
#     # Return the markers to be displayed on the map
#     return markers  # List of dl.Marker components


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)