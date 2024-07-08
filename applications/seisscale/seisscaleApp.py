from dash import html, dcc, callback, Output, Input, State, callback_context
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import base64
import io
from applications.seisscale.seisscaleFunctions import targetSpectrum, recordSelection, amplitudeScaling
from applications.asce.asceFunctions import getAsceDataMulti, getAsceDataMultiMCEr, getAsceDataTwo, getAsceDataTwoMCEr
from components.navbar import navbar

# title
seisScaleTitle = dmc.Text("🚀 SeisScale", className='fs-3 mx-3 mb-1 mt-3')

# default figure
defaultFig = go.Figure()
defaultFig.update_xaxes(
        title_text='Period (sec)',
        range=[0, 4],
        tickvals=np.arange(0, 4.5, 0.5),
        dtick=1,
        showgrid=True,
        zeroline=True,
        zerolinewidth=1
)

defaultFig.update_yaxes(
    title_text='pSa (g)',
    range=[0, 3],
    showgrid=True,
    zeroline=True,
    zerolinewidth=1
)

defaultFig.update_layout(
    showlegend=True, 
    template = "plotly_dark",
    paper_bgcolor = "#222222",
    plot_bgcolor = "#222222", 
    height=580, 
    title_text='No Data', 
    title_x=0.5, 
    legend=dict(
        yanchor="top",
        x=1,
        xanchor="right"
    )
)

# tbec input area
tbecInputArea = html.Div([
    dbc.Label("Spectral Acceleration at Short Periods (Ss)", className="mb-1 mt-1 mx-1"),
    dbc.Input(type = "number", id='ssInput', value=1.20, className="mb-2 mt-1"),
    dbc.Label("Spectral Acceleration at 1 sec (S1)", className="mb-1 mt-1 mx-1"),
    dbc.Input(type = "number", id='s1Input', value=0.25, className="mb-2 mt-1"),
    dbc.Label("Soil Type", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id = 'soilTypeInput', options = ['ZA', 'ZB', 'ZC', 'ZD', 'ZE'], value = 'ZC',  clearable=False, className="mb-2 mt-1 text-black"),
], style={'display': 'block'}, id='tbecInputArea')

# asce input area
asceInputArea = html.Div([
    dbc.Label("Spectrum Type", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id='spectrumTypeInput', 
                options = ['Multi Period Design Spectrum', 'Multi Period MCEr Design Spectrum', 'Two Period Design Spectrum', 'Two Period MCEr Design Spectrum'], 
                value = 'Multi Period Design Spectrum', clearable=False, className="mb-2 mt-1 text-black"),
    dbc.Label("Latitude", className="mb-1 mt-1 mx-1"),
    dbc.Input(type = "number", id='latitudeInput', value=32.23, className="mb-2 mt-1"),
    dbc.Label("Longitude", className="mb-1 mt-1 mx-1"),
    dbc.Input(type = "number", id='longitudeInput', value=-94.49, className="mb-2 mt-1"),
    dbc.Label("Site Category", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id='asceSiteCategoryInput', options = ['A', 'B', 'C', 'D', 'E'], value = 'C', clearable=False, className="mb-2 mt-1 text-black"),
], style={'display': 'none'}, id='asceInputArea')

# user-defined input area
userDefinedInputArea = html.Div([
    dbc.Alert([
        "ℹ️ Please consider the example CSV file.",
        dbc.Button("Download Example CSV File", id='downloadExampleButton', className="btn btn-secondary d-block mt-2")
    ], color="light", className="mx-2"),
    dcc.Upload(
        id='uploadCSVButton',
        children=html.Button('Upload CSV File', className='btn btn-secondary w-100'),
        style = {
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
        },
        multiple=False
    ),
    dmc.Text(id = 'uploadStatus', children=['No file has been uploaded.'], className="mt-2")
], style={'display': 'none'}, id='userInputArea')

# response input
responseTypeInput = html.Div([
    dbc.Label("Spectrum Definition", className="mb-1 mt-2 mx-2"),
    dcc.Dropdown(id="spectrumDefinitionInput", options = ['TBEC-2018', 'ASCE7-22', 'User-Defined'], value = 'TBEC-2018', clearable=False, className="mb-3 mt-2 mx-2 text-black"),
], style={'display': 'block'}, id = 'responseTypeInputArea')

responseButton = html.Div([
    dbc.Button("Create Response Spectrum", id='responseButton', color='primary', className="mb-2 mt-3"),
])

filterInput = html.Div([
    dbc.Label("Structure Period (sec)", className="mb-1 mt-2 mx-1"),
    dbc.Input(type = "number", id="periodInput", value=1, className="mb-2 mt-1"),
    dbc.Label("Magnitude Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "magnitudeRangeInput",
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
    dbc.Label("VS30 Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "vs30RangeInput",
                value=[360, 760],
                marks=[
                    {"value": 0, "label": "0"},
                    {"value": 1500, "label": "1500"}
                ],
                min=0,
                max=1500,
                step=10,
                minRange=20,
                precision=0,
                showLabelOnHover=True,
                className="mt-2 mb-4"
            ),
    dbc.Label("RJB Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "rjbRangeInput",
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
    dbc.Label("Fault Mechanism", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id="faultMechanismInput", 
                options = ['Strike-Slip', 'Normal', 'Reverse', 'Oblique', 'Reverse-Oblique', 'Normal-Oblique'], 
                value = 'Strike-Slip', 
                clearable=False, 
                className="mb-2 mt-1 text-black"
            ),
    dbc.Label("%5-%75 Duration Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "575DurationInput",
                value=[0, 500],
                marks=[
                    {"value": 0, "label": "0"},
                    {"value": 500, "label": "500"}
                ],
                min=0,
                max=500,
                step=5,
                minRange=10,
                precision=0,
                showLabelOnHover=True,
                className="mt-2 mb-4"
            ),
    dbc.Label("%5-%95 Duration Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "595DurationInput",
                value=[0, 500],
                marks=[
                    {"value": 0, "label": "0"},
                    {"value": 500, "label": "500"}
                ],
                min=0,
                max=500,
                step=5,
                minRange=10,
                precision=0,
                showLabelOnHover=True,
                className="mt-2 mb-4"
            ),
    dbc.Label("Arias Intensity Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "ariasIntensityInput",
                value=[0, 10],
                marks=[
                    {"value": 0, "label": "0"},
                    {"value": 10, "label": "10"}
                ],
                min=0,
                max=10,
                step=0.1,
                minRange=1,
                precision=0,
                showLabelOnHover=True,
                className="mt-2 mb-4"
            ),
    dbc.Button("Filter Ground Motions", id='filterMotionsButton', color='primary', className="mb-2 mt-2"),
    html.Br(),
    dbc.Label("Number of Ground Motions to be Scaled", className="mb-1 mt-2 mx-1"),
    dbc.Input(type = "number", id="numberOfMotionsInput", value=11, className="mb-2 mt-1"),
    dbc.Button("Find Optimum Selected Ground Motions", id='findOptimumButton', color='primary', className="mb-2 mt-2"),
])

scaleInput = html.Div([
    dbc.Label("Spectral Ordinate", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id="spectralOrdinateInput", 
                options = ['SRSS', 'RotD50', 'RotD100'], 
                value = 'SRSS', 
                clearable=False, 
                className="mb-2 mt-1 text-black"
            ),
    dbc.Label("Target Spectrum Shift", className="mb-1 mt-2 mx-1"),
    dbc.Input(type = "number", id="targetShiftInput", value=1.30, className="mb-2 mt-1"),
    dbc.Label("Period Range of Interest Coefficients", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
                id = "rangeCoeffInput",
                value=[0.20, 1.50],
                marks=[
                    {"value": 0.0, "label": "0.0"},
                    {"value": 3.0, "label": "3.0"}
                ],
                min=0.0,
                max=3.0,
                step=0.1,
                minRange=0.1,
                precision=2,
                showLabelOnHover=True,
                className="mt-2 mb-4"
            ),
    dbc.Button("Perform Amplitude Scaling", id='amplitudeScalingInput', color='primary', className="mb-2 mt-2"),
])

initialInputArea = html.Div([responseTypeInput, tbecInputArea, asceInputArea, userDefinedInputArea, responseButton], id="initialInputArea")

# create input section
body = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Tabs(
                                [
                                    dbc.Tab(html.Div(children=[initialInputArea], id='responseArea'), label="Response"),
                                    dbc.Tab(filterInput, label="Filtering"),
                                    dbc.Tab(scaleInput, label="Scaling"),

                                ],
                                className='nav-fill w-100'
                            )
                        ], className="inputArea mx-2 mb-2 mt-2"),
                className="inputForm mx-2 mt-4 mb-4")
        ], width=4),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=defaultFig, id="defaultFig", style={'marginTop': '-30px'}))
                ]),
            dbc.Row([
                html.Div(id='outputTable')
            ])
        ], width=8)
    ], className="mx-1")
)

def layout():
    return html.Div([
            navbar, 
            seisScaleTitle,
            body,
            dcc.Download(id="downloadExample")
        ])
    
    
