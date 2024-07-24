from datetime import datetime, date, timedelta
import numpy as np
from pandas import DataFrame
from applications.seisEvents.ids import DRAWERBUTTON, DRAWERFANCY
from applications.seisEvents.seisEventsFunctions import AfadEventsToDataFrame, DepthFilter, FDSN_EventsToDataFrame, GetAfadEvents2, GetFDSNEventsLastTwoDays, MagnitudeFilter, USGS_EventsDataToDataFrame,GetUSGSEvents
import dash_bootstrap_components as dbc
from dash import dcc,html,Input, Output,dash_table,callback,no_update
from dash.dependencies import Input, Output
import dash_leaflet as dl
import dash_mantine_components as dmc
from dash_iconify import DashIconify
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

# title
Title = dmc.Text(html.H2("SEISEVENTS"), className='fs-3 mx-3 mb-3 mt-3')

# Colorbar control for earthquake events locations
# =======================================================================================================

def create_colorscale(color1 : str, color2 : str, n_colors : int)->list:
    color1_ = [int(i) for i in color1[4:-1].split(",")]
    color2_ = [int(i) for i in color2[4:-1].split(",")]
    colors_ = np.linspace(start=color1_, stop=color2_, num=n_colors)
    colors  = [str(f"rgb{int(i[0]), int(i[1]), int(i[2])}") for i in colors_]
    return colors

classes=[10,20,40,60,80,100,120]
# ylorrd "Viridis"

# colorscale=create_colorscale(color1='rgb(255, 255, 204)', color2='rgb(128, 0, 38)', n_colors=7)
colorscale='ylorrd'
style     = dict(weight=2, opacity=0.7, color='black', dashArray='3')
vmin = 0
vmax = 120
# colorBars = dl.Colorbar(position="bottomright",colorscale=colorscale,min=vmin, max=vmax, unit='/km')
# Create colorbar.
ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+km".format(classes[-1])]
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
info = html.Div(children=Get_Info(), id="info", className="info", style={"position" : "absolute", "top" : "430px", "left" : "10px", "zIndex" : "9000"})



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
# Mag = MagnitudeFilter(MinMag=0.,MaxMag=10.)
# Depth = DepthFilter(MinDepth=0., MaxDepth=5000.)
usgs_geojson = GetUSGSEvents()
afad_geojson = GetAfadEvents2(FormatType='GEOJSON')
# fdsn_catalog = GetFDSNEventsLastTwoDays()

df_usgs      = USGS_EventsDataToDataFrame(usgs_geojson)
# df_fdsn      = FDSN_EventsToDataFrame(fdsn_catalog)
df_afad      = AfadEventsToDataFrame(afad_geojson)

# Javascript code : How to draw marker and which style
# =======================================================================================
on_each_feature_AFADevents = assign("""function(features, layer, context){
                                                                    layer.bindPopup(`
                                                                                        <div id='MarkerPopup' class="container" style:"flex-row align-center">
                                                                                            <div class="row">
                                                                                                <div class:"col align-center">
                                                                                                    <h2 style="margin: 0; margin-right: .5rem; font-size: xl; color: red;"> 
                                                                                                                <span style="margin: 0; font-size: small;"> ${features.properties.Type} <span/>
                                                                                                                ${features.properties.Magnitude}
                                                                                                    </h2>
                                                                                                </div>
                                                                                                
                                                                                                
                                                                                                <div class='class="col align-center"'>
                                                                                   
                                                                                                        <h4 style="margin:0.">Latidude :${features.geometry.coordinates[0]} Longitude : ${features.geometry.coordinates[1]}</h4>
                                                                                                        
                                                                                                        <h4 style="margin:0.">Depth : ${features.properties.Depth}-km</h4>                     
                                                                                                        
                                                                                                        <a href="https://deprem.afad.gov.tr/apiv2/event/filter?eventid=${features.properties.EventID} " target=_blank style="margin:0."> Details </a>
                                                                                                </div>   
                                                                                             </div>
                                                                                        </div>
                                                                                    `)
                                                                    }
                                """)

on_each_feature_USGSevents = assign("""function(features, layer, context){
                                                                    layer.bindPopup(`
                                                                                        <div id='MarkerPopup' class="container" style:"flex-row align-center">
                                                                                            <div class="row">
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
                                                                                        </div>
                                                                                    `)
                                                                    }
                                """)


point_to_layer_USGSevents = assign("""function(feature, latlng, context){
    
    const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
    circleOptions.fillColor = csc(feature.properties.depth);  // set color based on color prop
    circleOptions.radius    = feature.properties.mag * 2;  // set color based on color prop
    
    return new L.circleMarker(latlng,circleOptions);  // render a simple circle marker
}""")

point_to_layer_AFADevents = assign("""function(features, latlng, context){
    
    const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
    circleOptions.fillColor = csc(features.properties.Depth);  // set color based on color prop
    circleOptions.radius    = features.properties.Magnitude * 2;  // set color based on color prop
    
    return new L.circleMarker(latlng,circleOptions);  // render a simple circle marker
}""")

# geojson options ["pointToLayer", "style", "onEachFeature", "filter", "coordsToLatLng"]
# from dash_extensions.javascript import Namespace
# ns = Namespace("dashExtensions","default")
events_usgs = dl.GeoJSON(data=usgs_geojson,
                    cluster=True,
                    superClusterOptions={"radius": 60},
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    zoomToBoundsOnClick=True, # when true, zooms to bounds of feature (e.g. cluster) on click
                    
                    options=dict(pointToLayer = point_to_layer_USGSevents,
                                 onEachFeature=on_each_feature_USGSevents),
                    id='EventsUSGS',
                    hideout=dict(
                                 colorProp='depth',
                                 circleOptions=dict(fillOpacity = 0.6,stroke=True, weight = 1),
                                 min=vmin, 
                                 max=vmax, 
                                 colorscale=colorscale),
                    )

events_afad = dl.GeoJSON(data=afad_geojson[0],
                    cluster=True,
                    superClusterOptions={"radius": 60},
                    zoomToBounds=True,  # when true, zooms to bounds when data changes
                    zoomToBoundsOnClick=True, # when true, zooms to bounds of feature (e.g. cluster) on click
                    
                    options=dict(pointToLayer = point_to_layer_AFADevents,
                                 onEachFeature=on_each_feature_AFADevents),
                    id='EventsUSGS',
                    hideout=dict(
                                 colorProp='depth',
                                 circleOptions=dict(fillOpacity = 0.6,stroke=True, weight = 1),
                                 min=vmin, 
                                 max=vmax, 
                                 colorscale=colorscale),
                    )

# Create Layout
# =======================================================================================================

datePicker = dmc.Group( 
                        [
                            
                            dmc.DatePicker(
                                                id="datepicker-error",
                                                value=datetime.now().date()- timedelta(days=2),
                                                label="Start Date",
                                                required=True,
                                                clearable=False,
                                                w=200,
                                        ),
                                                
                            dmc.DatePicker(
                                                id="datepicker-error",
                                                value=datetime.now().date(),
                                                label="End Date",
                                                required=True,
                                                clearable=False,
                                                w=200,
                                        )
                                                
                            
                        ]
                        
                    )

dropDown = html.Div([
                        dbc.Label("Earthquake Web Services"),
                        dcc.Dropdown(id="webservice", options=["USGS", "AFAD"], value="USGS", clearable=False, className="mb-2 mt-1 text-black")
    ])

magRangeSlider = html.Div([
                        dbc.Label("Magnitude Range"),
                        dmc.RangeSlider(
                                        id="magnitudeRangeInput",
                                        value=[3.0, 10.0],
                                        marks=[
                                            {"value": 0.0, "label": "0"},
                                            {"value": 12.0, "label": "12"}
                                        ],
                                        min=0.0,
                                        max=12.0,
                                        step=0.1,
                                        minRange=0.5,
                                        precision=1,
                                        showLabelOnHover=True,
                                        className="mt-2 mb-4"
                                    ),
                    ])

buttonSearch = html.Div(dmc.Button("Search", id="event-search-button", loaderProps=dict(type = "dots"), variant="gradient"), className="d-grid gap-2 d-md-flex justify-content-md-end")

stack = dmc.Stack(children=[datePicker,
                    html.P(),
                    dropDown,
                    html.P(),
                    magRangeSlider,
                    html.P(),
                    buttonSearch],
                  spacing="xs")
filter = html.Div([
                    
                    stack
                    
            ])

#TODO Bilgi girişi için ilk aşamada drawer koydum belki direk ekrana gömülü bir formda hazırlanabilir. Buradaki veri girişine göre hem harita hemde tablo güncellenmeli.
drawer = html.Div(
                    [
                        # dmc.Button("Open Drawer", id="drawer-demo-button"),
                        dmc.ActionIcon(
                                        DashIconify(icon="clarity:settings-line", width=20),
                                                    size="lg",
                                                    variant="filled",
                                                    id="drawer-demo-button",
                                                    n_clicks=0,
                                                    mb=10,
                                                ),
                        dmc.Drawer( children=[
                                                filter
                                                
                                            ],
                                    title="Search Earthquake",
                                    id="drawer-simple",
                                    padding="md",
                                    size = 500,
                                    zIndex=10000,
                                ),
                    ]
                )


layersControl = dl.LayersControl([
                                    # BaseMap gösterim layer ı
                                    dl.Overlay(
                                        dl.LayerGroup(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}.png",id="TileMap")
                                        ),
                                        name="BaseMap",
                                        checked=False
                                        ),
                                    #TODO Ülke sınırlarını layer içerisine gömdüm opsiyonel olarak açılabiliyor bunu belki direk haritaya gömebiliriz
                                    #BUG ülke sınırlarını açınca deprem verilerinin üzerine çıkıyor ve tıklanamaz hale geliyor. zIndex tanımlaması olayo çözmedi buradaki problem js kodları içerisinde bunu açınsa en öne bunu koyması.
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
                                ])

map_Div = html.Div([
                    html.Div(
                                [
                                    dl.Map( id='map',
                                           center = [0,0],
                                           zoom = 4,
                                           doubleClickZoom=True,
                                           dragging=True,
                                           style={'width': '100%', 'height': '500px', 'margin': "auto"},
                                           children=[  dl.TileLayer(),
                                                        dl.FullScreenControl(),
                                                        dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",activeColor="#214097", completedColor="#972158"),
                                                        events_usgs,
                                                        layersControl,
                                                        colorbar,
                                                    ],
                                            )
                                    
                                ],
                                
                                id='map_div', 
                                className='map_div'
                            )
                ],
        className='main_div')

#TODO tablo ile ilgili görselleştirme ayarları yapılmalı. Tablodaki filtreleme,sıralama vb işlemler client tarafında mı yoksa backendde python ile mi yapılacak. Büyük veride client tarafı yavaş kalır, pythona geçmek lazım.
table = dbc.Container(
    [
                        # dbc.Label('Click a cell in the table:'),
                        # dash_table.DataTable(
                        #                         df_usgs.to_dict('records'),
                        #                         [{"name": i, "id": i} for i in df_usgs.columns], 
                        #                         id='tbl',
                        #                         page_current=0,
                        #                         page_size=20,
                        #                         page_action='custom',

                        #                         filter_action='custom',
                        #                         filter_query='',

                        #                         sort_action='custom',
                        #                         sort_mode='multi',
                        #                         sort_by=[],
                                                
                        #                         style_cell_conditional=[
                        #                                                     {
                        #                                                         'if': {'column_id': c},
                        #                                                         'textAlign': 'left'
                        #                                                     } for c in ['mag', 'depth']
                        #                                                 ],                                               
                        #                         style_header={
                        #                                         'backgroundColor': 'rgb(210, 210, 210)',
                        #                                         'color': 'black',
                        #                                         'fontWeight': 'bold'
                        #                                     },
                        #                         style_data_conditional=[
                        #                                                 {
                        #                                                     'if': {'filter_query': '{{mag}} = {}'.format(df_usgs['mag'].max()) },
                        #                                                                 'backgroundColor': '#0074D9',
                        #                                                                 'color': 'white'
                        #                                                 },
                                                                        
                        #                                                 {
                        #                                                     'if': {
                        #                                                         'filter_query': '{{mag}} = {}'.format(df_usgs['mag'].max()),
                        #                                                     },
                        #                                                         'color': 'tomato',
                        #                                                         'fontWeight': 'bold'
                        #                                                 },
                        #                                                 {
                        #                                                     'if':{'row_index' : 'odd'},
                        #                                                         'backgroundColor':'rgb(220,220,220)'
                        #                                                 }
                        #                                             ]
                        #                     ),
                        # dbc.Alert(id='tbl_out'),
                        dash_table.DataTable(
                                                id='datatable-interactivity',
                                                columns=[
                                                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in df_usgs.columns
                                                ],
                                                data=df_usgs.to_dict('records'),
                                                editable=True,
                                                filter_action="native",
                                                sort_action="native",
                                                sort_mode="multi",
                                                column_selectable="single",
                                                row_selectable="multi",
                                                row_deletable=True,
                                                selected_columns=[],
                                                selected_rows=[],
                                                page_action="native",
                                                page_current= 0,
                                                page_size= 10,
                                            ),
                    ]
                      ,id='table-events')

container = html.Div(children=[dbc.Row(Title),
                                dbc.Container(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(drawer, md=3),
                                                            dbc.Col(children=[map_Div], md=9),
                                                        ],
                                                        align="center",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(children=[table], md=9),
                                                        ],
                                                        align="center",
                                                    ),
                                                ],
                                                fluid=True,
                                            )
    ])

def layout():
    return html.Div([container])



# Callback functions
# =======================================================================================================

# Map controls
# =======================================================================================
#BUG Ülke sınırları kapalı olduğu halde gözüküyor. 
@callback(Output("info","children"), Input("county","hover_feature"))
def info_hover(feature):
    return Get_Info(feature,headtext="Country")
      
@callback(Output("map","children"),Output("table-events","children"), Input("webservice","value"))
def update_map(value):
    children = []
    table_chd = []
    if value == 'USGS':
    
        children=[  dl.TileLayer(),
                    dl.FullScreenControl(),
                    dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",activeColor="#214097", completedColor="#972158"),
                    events_usgs,
                    layersControl,
                    colorbar,
                ]
        table_chd = [
                        dash_table.DataTable(
                                                            id='datatable-interactivity',
                                                            columns=[
                                                                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df_usgs.columns
                                                            ],
                                                            data=df_usgs.to_dict('records'),
                                                            editable=True,
                                                            filter_action="native",
                                                            sort_action="native",
                                                            sort_mode="multi",
                                                            column_selectable="single",
                                                            row_selectable="multi",
                                                            row_deletable=True,
                                                            selected_columns=[],
                                                            selected_rows=[],
                                                            page_action="native",
                                                            page_current= 0,
                                                            page_size= 10,
                                                        )
                    ]
    if value == 'AFAD':
    
        children=[  dl.TileLayer(),
                    dl.FullScreenControl(),
                    dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",activeColor="#214097", completedColor="#972158"),
                    events_afad,
                    layersControl,
                    colorbar,
                ]
        table_chd = [
                        dash_table.DataTable(
                                                            id='datatable-interactivity',
                                                            columns=[
                                                                {"name": i, "id": i, "deletable": True, "selectable": True} for i in df_afad.columns
                                                            ],
                                                            data=df_afad.to_dict('records'),
                                                            editable=True,
                                                            filter_action="native",
                                                            sort_action="native",
                                                            sort_mode="multi",
                                                            column_selectable="single",
                                                            row_selectable="multi",
                                                            row_deletable=True,
                                                            selected_columns=[],
                                                            selected_rows=[],
                                                            page_action="native",
                                                            page_current= 0,
                                                            page_size= 10,
                                                        )
                    ]
    return children,table_chd

# Table controls
# =======================================================================================
# @callback(Output('tbl_out', 'children'), Input('tbl', 'active_cell'))
# def update_graphs(active_cell):
#     return str(active_cell) if active_cell else "Click the table"

@callback(
    Output('datatable-interactivity', 'style_data_conditional'),
    Input('datatable-interactivity', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': { 'column_id': i },
        'background_color': '#D2F3FF'
    } for i in selected_columns]

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3

#BUG Pagination da en son sayfaya gitmiyor ve boş sayfalar oluşuyor.
@callback(
    Output('tbl', 'data'),
    Input('tbl', "page_current"),
    Input('tbl', "page_size"),
    Input('tbl', 'sort_by'),
    Input('tbl', 'filter_query'))
def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = df_afad
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
                                [col['column_id'] for col in sort_by],
                                ascending=[
                                    col['direction'] == 'asc'
                                    for col in sort_by
                                ],
                                inplace=False
                            )

    page = page_current
    size = page_size
    return dff.iloc[page * size: (page + 1) * size].to_dict('records')


# Drawer controls
# =======================================================================================

#TODO Hem başlangıç zamanı hem de bitiş zamanı için kontroller yazılmalı.
@callback(Output("datepicker-error", "error"), Input("datepicker-error", "value"))
def datepicker_error(date):
    day = datetime.strptime(date, "%Y-%M-%d").day
    month = int(date.split("-")[1])
    year = datetime.strptime(date, "%Y-%M-%d").year
    if year > datetime.now().year:
        return "Please select a valid year."
    if month > datetime.now().month:
        return "Please select a valid month."
    if day > datetime.now().day:
        return "Please select a valid day."
    return ""

@callback(
    Output("drawer-simple", "opened"),
    Input("drawer-demo-button", "n_clicks"),
    prevent_initial_call=True,
)
def drawer_demo(n_clicks):
    return True

