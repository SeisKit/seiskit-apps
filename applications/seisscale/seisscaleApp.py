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
    showgrid=True,
    zeroline=True,
    zerolinewidth=1,
    rangemode='tozero'
)

defaultFig.update_layout(
    showlegend=True, 
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white", 
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
    dbc.Input(type="number", id='ssInput', value=1.20, className="mb-2 mt-1"),
    dbc.Label("Spectral Acceleration at 1 sec (S1)", className="mb-1 mt-1 mx-1"),
    dbc.Input(type="number", id='s1Input', value=0.25, className="mb-2 mt-1"),
    dbc.Label("Soil Type", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id='soilTypeInput', options=['ZA', 'ZB', 'ZC', 'ZD', 'ZE'], value='ZC', clearable=False, className="mb-2 mt-1 text-black"),
], style={'display': 'block'}, id='tbecInputArea')

# asce input area
asceInputArea = html.Div([
    dbc.Label("Spectrum Type", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id='spectrumTypeInput', 
                options=['Multi Period Design Spectrum', 'Multi Period MCEr Design Spectrum', 'Two Period Design Spectrum', 'Two Period MCEr Design Spectrum'], 
                value='Multi Period Design Spectrum', clearable=False, className="mb-2 mt-1 text-black"),
    dbc.Label("Latitude", className="mb-1 mt-1 mx-1"),
    dbc.Input(type="number", id='latitudeInput', value=32.23, className="mb-2 mt-1"),
    dbc.Label("Longitude", className="mb-1 mt-1 mx-1"),
    dbc.Input(type="number", id='longitudeInput', value=-94.49, className="mb-2 mt-1"),
    dbc.Label("Site Category", className="mb-1 mt-1 mx-1"),
    dcc.Dropdown(id='asceSiteCategoryInput', options=['A', 'B', 'C', 'D', 'E'], value='C', clearable=False, className="mb-2 mt-1 text-black"),
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
        multiple=False
    ),
    dmc.Text(id='uploadStatus', children=['No file has been uploaded.'], className="mt-2")
], style={'display': 'none'}, id='userInputArea')

# response input
responseTypeInput = html.Div([
    dbc.Label("Spectrum Definition", className="mb-1 mt-3 mx-2"),
    dcc.Dropdown(id="spectrumDefinitionInput", options=['TBEC-2018', 'ASCE7-22', 'User-Defined'], value='TBEC-2018', clearable=False, className="mb-3 mt-2 mx-2 text-black"),
], style={'display': 'block'}, id='responseTypeInputArea')

responseButton = html.Div([
    dbc.Button("Create Response Spectrum", id='responseButton', color='primary', className="mb-2 mt-3"),
])

filterInput = html.Div([
    dbc.Label("Structure Period (sec)", className="mb-1 mt-3 mx-1"),
    dbc.Input(type="number", id="periodInput", value=1, className="mb-2 mt-1"),
    dbc.Label("Magnitude Range", className="mb-2 mt-4 mx-1"),
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
    dbc.Label("VS30 Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
        id="vs30RangeInput",
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
        id="rjbRangeInput",
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
                options=['Strike-Slip', 'Normal', 'Reverse', 'Oblique', 'Reverse-Oblique', 'Normal-Oblique'], 
                value='Strike-Slip', 
                clearable=False, 
                className="mb-2 mt-1 text-black"
            ),
    dbc.Label("%5-%75 Duration Range", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
        id="575DurationInput",
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
        id="595DurationInput",
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
        id="ariasIntensityInput",
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
    dbc.Input(type="number", id="numberOfMotionsInput", value=11, className="mb-2 mt-1"),
    dbc.Button("Find Optimum Selected Ground Motions", id='findOptimumButton', color='primary', className="mb-2 mt-2"),
])

scaleInput = html.Div([
    dbc.Label("Spectral Ordinate", className="mb-1 mt-3 mx-2"),
    dcc.Dropdown(id="spectralOrdinateInput", 
                options=['SRSS', 'RotD50', 'RotD100'], 
                value='SRSS', 
                clearable=False, 
                className="mb-2 mt-1 text-black"
            ),
    dbc.Label("Target Spectrum Shift", className="mb-1 mt-2 mx-1"),
    dbc.Input(type="number", id="targetShiftInput", value=1.30, className="mb-2 mt-1"),
    dbc.Label("Period Range of Interest Coefficients", className="mb-2 mt-4 mx-1"),
    dmc.RangeSlider(
        id="rangeCoeffInput",
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
                        children=[
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
        ], xs=12, sm=12, md=4, lg=4, xl=4),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=defaultFig, id="defaultFig", style={'marginTop': '-30px'}))
                ]),
            dbc.Row([
                html.Div(id='outputTable')
            ])
        ], xs=12, sm=12, md=8, lg=8, xl=8)
    ], className="mx-1")
)

def layout():
    return html.Div([
            navbar, 
            seisScaleTitle,
            body,
            dcc.Download(id="downloadExample")
        ])
    
# callback to update responseArea
@callback(
    [
        Output('tbecInputArea', 'style'),
        Output('asceInputArea', 'style'),
        Output('userInputArea', 'style'),
        Output('responseTypeInputArea', 'style')
    ],
    [
        Input('spectrumDefinitionInput', 'value')
    ]
)
def updateInputArea(type):
    if type == 'TBEC-2018':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    elif type == 'ASCE7-22':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}, {'display': 'block'}
    elif type == 'User-Defined':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, {'display': 'block'}
    
# callback for upload status
@callback(
    Output('uploadStatus', 'children'),
    Input('uploadCSVButton', 'contents'),
    Input('uploadCSVButton', 'filename'),
    prevent_initial_call = True
)
def uploadStatus(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
        
    try:
        if 'csv' in filename:
            userResponse = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            status = "Upload is successful! ✅"
        else:
            status = 'File format should be CSV❗'
    except Exception as e:
        status = 'An error occured while reading the file. Please take a look at the example CSV file format! ❌'
        
    return status

# callback to download csv
@callback(
    Output('downloadExample', 'data'),
    Input('downloadExampleButton', 'n_clicks'),
    prevent_initial_call = True
)
def downloadExample(click):
    csvFile = "applications/seisscale/data/exampleSpectrum.csv"
    df = pd.read_csv(csvFile)
    return dcc.send_data_frame(df.to_csv, "example_spectrum.csv")

# callback to create response spectrum
@callback(
    Output('defaultFig', 'figure', allow_duplicate=True),
    Input('responseButton', 'n_clicks'),
    State('spectrumDefinitionInput', 'value'),
    State('ssInput', 'value'),
    State('s1Input', 'value'),
    State('soilTypeInput', 'value'),
    State('spectrumTypeInput', 'value'),
    State('latitudeInput', 'value'),
    State('longitudeInput', 'value'),
    State('asceSiteCategoryInput', 'value'),
    State('uploadCSVButton', 'contents'),
    State('uploadCSVButton', 'filename'),
    State('defaultFig', 'figure'),
    prevent_initial_call = True
)
def createResponseSpectrum(click, type, ss, s1, soil, spectrumType, lat, lon, site, contents, filename, fig):
    if click is None:
        raise PreventUpdate
    
    # clean the graph
    fig['data'] = []
    fig['layout']['shapes'] = []
    
    # apply theme
    fig['layout']['paper_bgcolor'] = 'white'
    fig['layout']['plot_bgcolor'] = 'white'
    fig['layout']['template'] = 'plotly_white'
        
    lineColor = "#000080"

    if type == 'User-Defined':
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'csv' in filename:
                userResponse = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                status = "Upload is successful! ✅"
            else:
                status = 'File format should be CSV. ❗'
        except Exception as e:
            status = 'An error occured while reading the file. Please take a look at the example CSV file format. ❌'
                                
        userTrace = go.Scatter(
                x = userResponse['T'],
                y = userResponse['Sa'],
                line=dict(color=lineColor),
                name='User-Defined Response Spectrum'
            )
        fig['layout']['title'] = {
            'text': 'Response Spectrum',
            'x': 0.5,
            'xanchor': 'center'
        }
        fig['layout']['legend'] = {
            'x': 1,
            'xanchor': 'right',
            'yanchor': 'top'
        }
        
        fig['data'].append(userTrace)

    elif type == 'TBEC-2018':
        tbecResponse = targetSpectrum(ss, s1, soil)
        tbecTrace = go.Scatter(
            x = tbecResponse['T'],
            y = tbecResponse['Sa'],
            line=dict(color=lineColor),
            name='TBEC Response Spectrum'
        )
        fig['layout']['title'] = {
            'text': 'Response Spectrum',
            'x': 0.5,
            'xanchor': 'center'
        }
        fig['layout']['legend'] = {
            'x': 1,
            'xanchor': 'right',
            'yanchor': 'top'
        }
    
        fig['data'].append(tbecTrace)
        
    elif type == 'ASCE7-22':
        if spectrumType == 'Multi Period Design Spectrum':
            asceResponse = getAsceDataMulti(lat, lon, 'III', site, 'Title')
            asceResponse = asceResponse.rename(columns={'multiPeriodDesignSpectrumPeriods': 'T', 'multiPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Multi Period MCEr Design Spectrum':
            asceResponse = getAsceDataMultiMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = asceResponse.rename(columns={'multiPeriodMCErSpectrumPeriods': 'T', 'multiPeriodMCErSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period Design Spectrum':
            asceResponse = getAsceDataTwo(lat, lon, 'III', site, 'Title')
            asceResponse = asceResponse.rename(columns={'twoPeriodDesignSpectrumPeriods': 'T', 'twoPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period MCEr Design Spectrum':
            asceResponse = getAsceDataTwoMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = asceResponse.rename(columns={'twoPeriodMCErSpectrumPeriods': 'T', 'twoPeriodMCErSpectrumOrdinates': 'Sa'})
        
        asceResponse['Sa'] = [x*9.81 for x in np.interp(asceResponse['T'], asceResponse['T'], asceResponse['Sa'])]
    
        asceTrace = go.Scatter(
            x = asceResponse['T'],
            y = asceResponse['Sa'],
            line=dict(color=lineColor),
            name='ASCE Response Spectrum'
        )
        fig['layout']['title'] = {
            'text': 'Response Spectrum',
            'x': 0.5,
            'xanchor': 'center'
        }
        fig['layout']['legend'] = {
            'x': 1,
            'xanchor': 'right',
            'yanchor': 'top'
        }
    
        fig['data'].append(asceTrace)

    return fig

# callback for filtering and finding optimum
@callback(
    Output('defaultFig', 'figure', allow_duplicate=True),
    [
        Input('filterMotionsButton', 'n_clicks'),
        Input('findOptimumButton', 'n_clicks'),
    ],
    [
        State('defaultFig', 'figure'),
        State('periodInput', 'value'),
        State('magnitudeRangeInput', 'value'),
        State('vs30RangeInput', 'value'),
        State('rjbRangeInput', 'value'),
        State('faultMechanismInput', 'value'),
        State('575DurationInput', 'value'),
        State('595DurationInput', 'value'),
        State('ariasIntensityInput', 'value'),
        State('numberOfMotionsInput', 'value'),
        State('spectrumDefinitionInput', 'value'),
        State('ssInput', 'value'),
        State('s1Input', 'value'),
        State('soilTypeInput', 'value'),
        State('spectrumTypeInput', 'value'),
        State('latitudeInput', 'value'),
        State('longitudeInput', 'value'),
        State('asceSiteCategoryInput', 'value'),
        State('uploadCSVButton', 'contents'),
        State('uploadCSVButton', 'filename'),
             
    ],
    prevent_initial_call = True
)
def filterFunction(clickFilter,clickOptimum, fig, period, magnitudeRange, vs30Range, rjgRange, faultMechanism, duration575, duration595, ariasIntensity, numberOfMotions, type, ss, s1, soil, spectrumType, lat, lon, site, contents, filename):
    
    # clean the fig
    fig['data'] = []
    fig['layout']['shapes'] = []
    
    # get triggered button id
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # apply theme
    fig['layout']['paper_bgcolor'] = 'white'
    fig['layout']['plot_bgcolor'] = 'white'
    fig['layout']['template'] = 'plotly_white'
        
    lineColor = "#000080"
 
    if type == 'User-Defined':
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'csv' in filename:
                userResponse = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                alert = "Upload is successful!"
            else:
                alert = 'File format should be CSV.'
        except Exception as e:
            alert = 'An error occured while reading the file. Please take a look at the example CSV file format.'
                    
        targetTrace = go.Scatter(
                x = userResponse['T'],
                y = userResponse['Sa'],
                line=dict(color=lineColor),
                name='User-Defined Response Spectrum'
            )
        
        selectedTarget = userResponse

    elif type == 'TBEC-2018':
        tbecResponse = targetSpectrum(ss, s1, soil)
        targetTrace = go.Scatter(
            x = tbecResponse['T'],
            y = tbecResponse['Sa'],
            line=dict(color=lineColor),
            name='TBEC Response Spectrum'
        )

        selectedTarget = tbecResponse
        
    elif type == 'ASCE7-22':
        tbecResponse = targetSpectrum(ss, s1, soil)
        timeIndex = tbecResponse['T']
        if spectrumType == 'Multi Period Design Spectrum':
            asceInit = getAsceDataMulti(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['multiPeriodDesignSpectrumPeriods'] = timeIndex
            asceResponse['multiPeriodDesignSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                    timeIndex, asceInit['multiPeriodDesignSpectrumPeriods'], asceInit['multiPeriodDesignSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'multiPeriodDesignSpectrumPeriods': 'T', 'multiPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Multi Period MCEr Design Spectrum':
            asceInit = getAsceDataMultiMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['multiPeriodMCErSpectrumPeriods'] = timeIndex
            asceResponse['multiPeriodMCErSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['multiPeriodMCErSpectrumPeriods'], asceInit['multiPeriodMCErSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'multiPeriodMCErSpectrumPeriods': 'T', 'multiPeriodMCErSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period Design Spectrum':
            asceInit = getAsceDataTwo(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['twoPeriodDesignSpectrumPeriods'] = timeIndex
            asceResponse['twoPeriodDesignSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['twoPeriodDesignSpectrumPeriods'], asceInit['twoPeriodDesignSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'twoPeriodDesignSpectrumPeriods': 'T', 'twoPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period MCEr Design Spectrum':
            asceInit = getAsceDataTwoMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['twoPeriodMCErSpectrumPeriods'] = timeIndex
            asceResponse['twoPeriodMCErSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['twoPeriodMCErSpectrumPeriods'], asceInit['twoPeriodMCErSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'twoPeriodMCErSpectrumPeriods': 'T', 'twoPeriodMCErSpectrumOrdinates': 'Sa'})
        
        targetTrace = go.Scatter(
            x = asceResponse['T'],
            y = asceResponse['Sa'],
            line=dict(color=lineColor),
            name='ASCE Response Spectrum'
        )
        selectedTarget = asceResponse
    
    # a logic for tuple to string
    def tupleToStr(tup):
            return '{value1} {value2}'.format(value1=tup[0], value2=tup[1])
        
    if triggered_id == 'filterMotionsButton':
            
        # clean the fig
        fig['data'] = []
        fig['layout']['shapes'] = []
    
        selected_keys, eqe_selected_x, eqe_selected_y, rsn_selected, t, eqe_s = recordSelection(
                                                                                            tupleToStr(magnitudeRange),
                                                                                            tupleToStr(vs30Range),
                                                                                            tupleToStr(rjgRange),
                                                                                            faultMechanism,
                                                                                            tupleToStr(duration575),
                                                                                            tupleToStr(duration595),
                                                                                            tupleToStr(ariasIntensity),
                                                                                            selectedTarget,
                                                                                            "Any",
                                                                                            period,
                                                                                            numberOfMotions
                                                                                            )
        
        for name in rsn_selected:
            filteredTrace_x = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_x[name],
                line=dict(color='gray', width=0.3), showlegend=False
            )
            filteredTrace_y = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_y[name],
                line=dict(color='gray', width=0.3), showlegend=False
            )
            fig['data'].append(filteredTrace_x)
            fig['data'].append(filteredTrace_y)
            
        fig['layout']['title'] = {
            'text': 'Filtered Records',
            'x': 0.5,
            'xanchor': 'center'
        }
        
        fig['layout']['legend'] = {
                'x': 1,
                'xanchor': 'right',
                'yanchor': 'top'
        }
        fig['data'].append(targetTrace)
        
        return fig
    
    elif triggered_id == 'findOptimumButton':
        
        selected_keys, eqe_selected_x, eqe_selected_y, rsn_selected, t, eqe_s = recordSelection(
                                                                                            tupleToStr(magnitudeRange),
                                                                                            tupleToStr(vs30Range),
                                                                                            tupleToStr(rjgRange),
                                                                                            faultMechanism,
                                                                                            tupleToStr(duration575),
                                                                                            tupleToStr(duration595),
                                                                                            tupleToStr(ariasIntensity),
                                                                                            selectedTarget,
                                                                                            "Any",
                                                                                            period,
                                                                                            numberOfMotions
                                                                                            )
        
        for name in selected_keys:
            selectedTrace_x = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_x[name],
                line=dict(color='gray', width=0.4), showlegend=False
            )
            selectedTrace_y = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_y[name],
                line=dict(color='gray', width=0.4), showlegend=False
            )
            fig['data'].append(selectedTrace_x)
            fig['data'].append(selectedTrace_y)
            
        fig['layout']['title'] = {
            'text': 'Optimum Selected Records',
            'x': 0.5,
            'xanchor': 'center'
        }
        
        fig['layout']['legend'] = {
                'x': 1,
                'xanchor': 'right',
                'yanchor': 'top'
        }
        fig['data'].append(targetTrace)
        
        return fig
    
# callback for scaling
@callback(
    Output('defaultFig', 'figure', allow_duplicate=True),
    Output('outputTable', 'children'),
    Input('amplitudeScalingInput', 'n_clicks'),
    [
        State('periodInput', 'value'),
        State('magnitudeRangeInput', 'value'),
        State('vs30RangeInput', 'value'),
        State('rjbRangeInput', 'value'),
        State('faultMechanismInput', 'value'),
        State('575DurationInput', 'value'),
        State('595DurationInput', 'value'),
        State('ariasIntensityInput', 'value'),
        State('numberOfMotionsInput', 'value'),
        State('spectrumDefinitionInput', 'value'),
        State('ssInput', 'value'),
        State('s1Input', 'value'),
        State('soilTypeInput', 'value'),
        State('spectrumTypeInput', 'value'),
        State('latitudeInput', 'value'),
        State('longitudeInput', 'value'),
        State('asceSiteCategoryInput', 'value'),
        State('uploadCSVButton', 'contents'),
        State('uploadCSVButton', 'filename'),
        State('spectralOrdinateInput', 'value'),
        State('targetShiftInput', 'value'),
        State('rangeCoeffInput', 'value'),        
        State('defaultFig', 'figure'),
    ],
    prevent_initial_call = True
)
def performScaling(click, period, magnitudeRange, vs30Range, rjgRange, faultMechanism, duration575, duration595, ariasIntensity, numberOfMotions, type, ss, s1, soil, spectrumType, lat, lon, site, contents, filename, ordinate, shift, range, fig):
    
    # clean the fig
    fig['data'] = []
    fig['layout']['shapes'] = []
    
    # apply theme
    fig['layout']['paper_bgcolor'] = 'white'
    fig['layout']['plot_bgcolor'] = 'white'
    fig['layout']['template'] = 'plotly_white'
        
    responseColor = "#000080"
    geoMeanColor = 'darkorange'
    meanColor = 'red'
    fillColor = 'yellow'
        
    # a logic for tuple to string
    def tupleToStr(tup):
            return '{value1} {value2}'.format(value1=tup[0], value2=tup[1])
    
    # get selected target
    if type == 'User-Defined':
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'csv' in filename:
                userResponse = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                alert = "Upload is successful!"
            else:
                alert = 'File format should be CSV.'
        except Exception as e:
            alert = 'An error occured while reading the file. Please take a look at the example CSV file format.'
                    
        targetTrace = go.Scatter(
                x = userResponse['T'],
                y = userResponse['Sa'],
                line=dict(color=responseColor),
                name='User-Defined Response Spectrum'
            )
        
        selectedTarget = userResponse

    elif type == 'TBEC-2018':
        tbecResponse = targetSpectrum(ss, s1, soil)
        targetTrace = go.Scatter(
            x = tbecResponse['T'],
            y = tbecResponse['Sa'],
            line=dict(color=responseColor),
            name='TBEC Response Spectrum'
        )

        selectedTarget = tbecResponse
        
    elif type == 'ASCE7-22':
        tbecResponse = targetSpectrum(ss, s1, soil)
        timeIndex = tbecResponse['T']
        if spectrumType == 'Multi Period Design Spectrum':
            asceInit = getAsceDataMulti(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['multiPeriodDesignSpectrumPeriods'] = timeIndex
            asceResponse['multiPeriodDesignSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                    timeIndex, asceInit['multiPeriodDesignSpectrumPeriods'], asceInit['multiPeriodDesignSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'multiPeriodDesignSpectrumPeriods': 'T', 'multiPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Multi Period MCEr Design Spectrum':
            asceInit = getAsceDataMultiMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['multiPeriodMCErSpectrumPeriods'] = timeIndex
            asceResponse['multiPeriodMCErSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['multiPeriodMCErSpectrumPeriods'], asceInit['multiPeriodMCErSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'multiPeriodMCErSpectrumPeriods': 'T', 'multiPeriodMCErSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period Design Spectrum':
            asceInit = getAsceDataTwo(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['twoPeriodDesignSpectrumPeriods'] = timeIndex
            asceResponse['twoPeriodDesignSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['twoPeriodDesignSpectrumPeriods'], asceInit['twoPeriodDesignSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'twoPeriodDesignSpectrumPeriods': 'T', 'twoPeriodDesignSpectrumOrdinates': 'Sa'})
        elif spectrumType == 'Two Period MCEr Design Spectrum':
            asceInit = getAsceDataTwoMCEr(lat, lon, 'III', site, 'Title')
            asceResponse = pd.DataFrame()
            asceResponse['twoPeriodMCErSpectrumPeriods'] = timeIndex
            asceResponse['twoPeriodMCErSpectrumOrdinates'] = [x*9.81 for x in np.interp(
                timeIndex, asceInit['twoPeriodMCErSpectrumPeriods'], asceInit['twoPeriodMCErSpectrumOrdinates'])]
            asceResponse = asceResponse.rename(columns={'twoPeriodMCErSpectrumPeriods': 'T', 'twoPeriodMCErSpectrumOrdinates': 'Sa'})
        
        targetTrace = go.Scatter(
            x = asceResponse['T'],
            y = asceResponse['Sa'],
            line=dict(color=responseColor),
            name='ASCE Response Spectrum'
        )
        selectedTarget = asceResponse
    
    
    # get selected ground motions
    selected_keys, eqe_selected_x, eqe_selected_y, rsn_selected, t, eqe_s = recordSelection(
                                                                                            tupleToStr(magnitudeRange),
                                                                                            tupleToStr(vs30Range),
                                                                                            tupleToStr(rjgRange),
                                                                                            faultMechanism,
                                                                                            tupleToStr(duration575),
                                                                                            tupleToStr(duration595),
                                                                                            tupleToStr(ariasIntensity),
                                                                                            selectedTarget,
                                                                                            "Any",
                                                                                            period,
                                                                                            numberOfMotions
                                                                                            )
    
    defaultFrame = pd.DataFrame(
                columns=["Record Sequence Number", "Earthquake Name", "Station Name", "Scale Factor"], 
                index=pd.RangeIndex(start=1, stop=numberOfMotions + 1, name='index'))
        
    eqe_s_filtered = eqe_s[eqe_s["RecordSequenceNumber"].isin(selected_keys)]
    defaultFrame["Earthquake Name"] = eqe_s_filtered["EarthquakeName"].to_list()
    defaultFrame["Station Name"] = eqe_s_filtered["StationName"].to_list()
    defaultFrame["Record Sequence Number"] = selected_keys
    
    if ordinate == 'SRSS':
    
        sf_dict, multiplied_selected_x, multiplied_selected_y, geo_mean_1st_scaled_df, srss_mean_df, srss_mean_scaled_df = amplitudeScaling(
                selected_keys, selectedTarget, period, shift, range[0], range[1], 'srss')
        
        defaultFrame["Scale Factor"] = list(sf_dict.values())
        
        for name in selected_keys:
            selected_trace_x = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_x[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            selected_trace_y = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_y[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            fig['data'].append(selected_trace_x)
            fig['data'].append(selected_trace_y)
        
        geoMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=geo_mean_1st_scaled_df["Mean"],
            name='Geometric Mean Scaled', 
            line=dict(color=geoMeanColor)
        )
        
        fig['data'].append(geoMeanTrace)
        
        srssMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=srss_mean_df['Mean'],
            name = 'SRSS Mean',
            line=dict(color=meanColor, dash='dash', width=2)
        )
        
        fig['data'].append(srssMeanTrace)
        
        srssMeanScaledTrace = go.Scatter(
            x = selectedTarget['T'],
            y = srss_mean_scaled_df['Mean'],
            name='SRSS Mean Scaled',
            line=dict(color=meanColor, width=2)
        )
        
        fig['data'].append(srssMeanScaledTrace)
        
        fig['data'].append(targetTrace)
        
        shiftedTargetTrace = go.Scatter(
            x = selectedTarget['T'],
            y = selectedTarget['Sa'] * shift,
            name = 'Shifted Target Spectrum',
            line=dict(color=responseColor, dash='dash')
        )
        
        fig['data'].append(shiftedTargetTrace)
        
        fig['layout']['title'] = {
            'text': 'Scaled Records',
            'x': 0.5,
            'xanchor': 'center'
        }
        
        fig['layout']['shapes'] = [
                {
                    'type': 'rect',
                    'xref': 'x',
                    'yref': 'paper',
                    'x0': range[0]*period,
                    'x1': range[1]*period,
                    'y0': 0,
                    'y1': 1,
                    'fillcolor': fillColor,
                    'opacity': 0.1,
                    'line': {
                        'width': 0,
                    },
                }
        ]
        
    elif ordinate == 'RotD50':
        
        sf_dict, multiplied_selected_x, multiplied_selected_y, geo_mean_1st_scaled_df, srss_mean_df, srss_mean_scaled_df = amplitudeScaling(
                selected_keys, selectedTarget, period, shift, range[0], range[1], 'rotd50')
        
        defaultFrame["Scale Factor"] = list(sf_dict.values())
        
        for name in selected_keys:
            selected_trace_x = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_x[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            selected_trace_y = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_y[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            fig['data'].append(selected_trace_x)
            fig['data'].append(selected_trace_y)
        
        geoMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=geo_mean_1st_scaled_df["Mean"],
            name='Geometric Mean Scaled', 
            line=dict(color=geoMeanColor)
        )
        
        fig['data'].append(geoMeanTrace)
        
        srssMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=srss_mean_df['Mean'],
            name = 'RotD50 Mean',
            line=dict(color=meanColor, dash='dash', width=2)
        )
        
        fig['data'].append(srssMeanTrace)
        
        srssMeanScaledTrace = go.Scatter(
            x = selectedTarget['T'],
            y = srss_mean_scaled_df['Mean'],
            name='RotD50 Mean Scaled',
            line=dict(color=meanColor, width=2)
        )
        
        fig['data'].append(srssMeanScaledTrace)
        
        fig['data'].append(targetTrace)
        
        shiftedTargetTrace = go.Scatter(
            x = selectedTarget['T'],
            y = selectedTarget['Sa'] * shift,
            name = 'Shifted Target Spectrum',
            line=dict(color=responseColor, dash='dash')
        )
        
        fig['data'].append(shiftedTargetTrace)
        
        fig['layout']['title'] = {
            'text': 'Scaled Records',
            'x': 0.5,
            'xanchor': 'center'
        }
        
        fig['layout']['shapes'] = [
                {
                    'type': 'rect',
                    'xref': 'x',
                    'yref': 'paper',
                    'x0': range[0]*period,
                    'x1': range[1]*period,
                    'y0': 0,
                    'y1': 1,
                    'fillcolor': fillColor,
                    'opacity': 0.1,
                    'line': {
                        'width': 0,
                    },
                }
        ]
        
    elif ordinate == 'RotD100':
        sf_dict, multiplied_selected_x, multiplied_selected_y, geo_mean_1st_scaled_df, srss_mean_df, srss_mean_scaled_df = amplitudeScaling(
                selected_keys, selectedTarget, period, shift, range[0], range[1], 'rotd100')
        
        
        defaultFrame["Scale Factor"] = list(sf_dict.values())
        
        for name in selected_keys:
            selected_trace_x = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_x[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            selected_trace_y = go.Scatter(
                x = selectedTarget['T'],
                y = eqe_selected_y[name],
                line=dict(color='gray', width=0.4),
                showlegend=False
            )
            fig['data'].append(selected_trace_x)
            fig['data'].append(selected_trace_y)
        
        geoMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=geo_mean_1st_scaled_df["Mean"],
            name='Geometric Mean Scaled', 
            line=dict(color=geoMeanColor)
        )
        
        fig['data'].append(geoMeanTrace)
        
        srssMeanTrace = go.Scatter(
            x=selectedTarget['T'],
            y=srss_mean_df['Mean'],
            name = 'RotD100 Mean',
            line=dict(color=meanColor, dash='dash', width=2)
        )
        
        fig['data'].append(srssMeanTrace)
        
        srssMeanScaledTrace = go.Scatter(
            x = selectedTarget['T'],
            y = srss_mean_scaled_df['Mean'],
            name='RotD100 Mean Scaled',
            line=dict(color=meanColor, width=2)
        )
        
        fig['data'].append(srssMeanScaledTrace)
        
        fig['data'].append(targetTrace)
        
        shiftedTargetTrace = go.Scatter(
            x = selectedTarget['T'],
            y = selectedTarget['Sa'] * shift,
            name = 'Shifted Target Spectrum',
            line=dict(color=responseColor, dash='dash')
        )
        
        fig['data'].append(shiftedTargetTrace)
        
        fig['layout']['title'] = {
            'text': 'Scaled Records',
            'x': 0.5,
            'xanchor': 'center'
        }
        
        fig['layout']['shapes'] = [
                {
                    'type': 'rect',
                    'xref': 'x',
                    'yref': 'paper',
                    'x0': range[0]*period,
                    'x1': range[1]*period,
                    'y0': 0,
                    'y1': 1,
                    'fillcolor': fillColor,
                    'opacity': 0.1,
                    'line': {
                        'width': 0,
                    },
                }
        ]

    # prepare the table
    table = dbc.Table.from_dataframe(defaultFrame, class_name="text-center")
    
    return fig, table