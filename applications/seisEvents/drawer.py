from datetime import datetime, timedelta
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import dcc,html

"""SIDEBAR_STYLE = {
    "position" : "fixed", 
    "top" : 0, 
    "left" : 0, 
    "bottom":0, 
    "width":"16rem", 
    "padding":"2rem 1rem", 
    "background-color" :"#f8f9fa"}


sideBar = html.Div([
                    html.H2("Filter", className="display-4"),
                    html.Hr(),
                    html.P(
                        "A simple sidebar layout with navigation links", className="lead"
                    ),
                    filter
                ],
    style=SIDEBAR_STYLE,)"""
    
def Create_Drawer()->html.Div:
    # Create Drawer
    # ======================================

    datePicker = dmc.Group( 
                            [
                                
                                dmc.DatePicker(
                                                    id="startDatePick",
                                                    value=datetime.now().date()- timedelta(days=2),
                                                    label="Start Date",
                                                    required=True,
                                                    clearable=False,
                                                    w=200,
                                            ),
                                                    
                                dmc.DatePicker(
                                                    id="endDatePick",
                                                    value=datetime.now().date(),
                                                    label="End Date",
                                                    required=True,
                                                    clearable=False,
                                                    w=200,
                                            )
                                                    
                                
                            ]
                            
                        )

    webServiceDropDown = html.Div([
                            #BUG Uyarı drawerın altında kaldığı için gözükmüyor net olarak. 
                            dmc.NotificationsProvider(zIndex=1),
                            html.Div(id="notifications-container"),
                            dmc.Text("Earthquake Web Services",
                                                    color="rgb(33,37,41)",
                                                    style={"font-size" : "14px"},
                                                    lh="1.55",
                                                    fw=500,
                                                    tt="capitalize",
                                                    ff='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',className="mb-2 mt-4 mx-1"),
                            dcc.Dropdown(id="webservice", options=["USGS", "AFAD"], value="USGS", clearable=False, className="mb-2 mt-1 text-black")
        ])

    depthSlider = html.Div(children=[
                                        dmc.Text("Depth Range",
                                                    color="rgb(33,37,41)",
                                                    style={"font-size" : "14px"},
                                                    lh="1.55",
                                                    fw=500,
                                                    tt="capitalize",
                                                    ff='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',className="mb-2 mt-4 mx-1"),
                                        dmc.RangeSlider(
                                                            id="depthInput",
                                                            value=[0, 3000],
                                                            marks=[
                                                                {"value": 0, "label": "0"},
                                                                {"value": 3000, "label": "3000"}
                                                            ],
                                                            min=0,
                                                            max=3000,
                                                            step=10,
                                                            minRange=20,
                                                            precision=0,
                                                            showLabelOnHover=True,
                                                            className="mt-2 mb-4"
                                                        ),
        ])

    magRangeSlider = html.Div([
                            dmc.Text("Magnitude Range",
                                    color="rgb(33,37,41)",
                                    style={"font-size" : "14px"},
                                    lh="1.55",
                                    fw=500,
                                    tt="capitalize",
                                    ff='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'),
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

    stack = dmc.Stack(children=[
                        webServiceDropDown,
                        # dmc.Divider(variant="solid", size="md"),
                        dmc.Space(h="md"),
                        datePicker,
                        dmc.Space(h="md"),
                        magRangeSlider,
                        dmc.Space(h="md"),
                        depthSlider,
                        dmc.Space(h="md"),
                        buttonSearch],
                    spacing="xs")

    filter = dmc.Card(children=[
                                    dmc.CardSection(
                                                    dmc.Group(dmc.Text("Filters",fw=700),
                                                            align="justify space-between"
                                                            ),
                                                    withBorder=True,
                                                    inheritPadding=True,
                                                    py="xs"
                                                ),
                                    
                                    dmc.CardSection(
                                                    dmc.Group(stack,align="justify space-between"),
                                                    withBorder=True,
                                                    inheritPadding=True,
                                                    py="xs"
                                                ),
                                    
                            ],
                    withBorder=True,
                    shadow="sm",
                    radius="xl",
                    h=550,
                    w=550
                    )
                    

    #TODO Bilgi girişi için ilk aşamada drawer koydum belki direk ekrana gömülü bir formda hazırlanabilir. Buradaki veri girişine göre hem harita hemde tablo güncellenmeli.
    drawer = html.Div(
                        [
                            # dmc.Button("Open Drawer", id="drawer-demo-button"),
                            
                            dmc.Drawer( children=[
                                                    filter
                                                    
                                                ],
                                        title="Search Earthquake",
                                        id="drawer-simple",
                                        padding="md",
                                        size = 600,
                                        zIndex=10000,
                                        transition='rotate-left', 
                                        transitionDuration = 150, 
                                        transitionTimingFunction = 'linear' 
                                    ),
                        ]
                    )

    return drawer


