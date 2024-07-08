import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State, callback, ctx, dash_table
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
import plotly.graph_objects as go
import pandas as pd
from applications.eqprocess.eqProcessFunctions import detrendFunction, filterFunction, ResponseSpectrum, ariasIntensityCreator, fourierTransform
from applications.eqprocess.record import AT2, ASC
from components.navbar import navbar
from io import BytesIO
import base64

processorTitle = dmc.Text("🌐 Earthquake Data Processor", className='fs-3 mx-4 mb-3 mt-3 text-center')

# set the data import area
dataImporter = dcc.Upload(
    id='uploadData',
    children=html.Div([
    dmc.Button(
        html.Div([
                html.Div("Upload or Drag and Drop File", className="mt-2 mx-2", style={'fontSize': '16px'}),
                html.Div("Limit 200MB per file • AT2, ASC", className="mt-2 mb-2 mx-2", style={'fontSize': '10px'}),
            ]),
        leftIcon=DashIconify(icon="clarity:upload-cloud-line", width=30),
        variant="link",
        color="blue",
        size="xl",
        radius='lg',
        className='w-100'
    ),
], className='d-flex justify-content-center align-items-center')
)

# output message for the user
uploadedFile = html.Div(id="outputFileName", className="mx-5 d-flex justify-content-center align-items-center")

# trimming function inputs
trimTab = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Trim Range", className="mb-2 mt-1 mx-1"),
            dmc.RangeSlider(
                        id = "trimRangeInput",
                        value=[0, 500],
                        marks=[
                            {"value": 0, "label": "0"},
                            {"value": 500, "label": "500"}
                        ],
                        min=0.0,
                        max=500.0,
                        step=0.1,
                        minRange=0.5,
                        precision=2,
                        showLabelOnHover=True,
                        className="mt-2 mb-4"
                    ),
            dbc.Button("Apply Trim", id="applyTrim", color="primary", className="mt-2"),
            dbc.Button("Reset", id="resetTrim", color="info", outline=True, className="mt-2 mx-2", style={'display': 'none'}),
        ]
    ),
    className="mt-1",
)

# detrend function inputs
detrendTab = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Detrend Method", className="mb-2 mt-1 mx-1"),
            dcc.Dropdown(id='detrendInput', options = ['Linear', 'Polynomial'], value = 'Linear', clearable=False, className="mb-2 mt-1 text-black"),
            dbc.Label("Order", className="mb-1 mt-1 mx-1", style={'display': 'none'}),
            dbc.Label("Order", id="orderLabel", className="mb-2 mt-1 mx-1", style={'display': 'none'}),
            dbc.Input(type = "number", id='orderInput', value=1, className="mb-2 mt-1", style={'display': 'none'}),
            dbc.Button("Apply Detrend", id="applyDetrend", color="primary", className="mt-2"),
        ]
    ),
    className="mt-1",
)

# filtering inputs
filterTab = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Filter Method", className="mb-2 mx-1"),
            dcc.Dropdown(id='filterMethodInput', options = ['Band-Pass', 'High-Pass', 'Low-Pass'], value = 'Band-Pass', clearable=False, className="mb-2 mt-1 text-black"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Low-Pass Corner", id="lowPassLabel", className="mb-2 mt-1 mx-1", style={'display': 'block'}),
                    dbc.Input(type="number", id='lowPassInput', value=0.5, className="mb-2 mt-1", style={'display': 'block'}),
                ], width=6),
                dbc.Col([
                    dbc.Label("High-Pass Corner", id="highPassLabel", className="mb-2 mt-1 mx-1", style={'display': 'block'}),
                    dbc.Input(type="number", id='highPassInput', value=25.0, className="mb-2 mt-1", style={'display': 'block'}),
                ], width=6),
            ], className="mb-1"),
            dbc.Label("Order", id="filterOrderLabel", className="mb-2 mt-1 mx-1"),
            dbc.Input(type = "number", id='filterOrderInput', value=4, className="mb-2 mt-1"),
            dbc.Button("Apply Filter", id="applyFilter", color="primary", className="mt-2"),
        ]
    ),
    className="mt-1",
)

# set the default figure
signalFig = go.Figure()
signalFig.update_xaxes(
    title_text="Time",
)
signalFig.update_yaxes(
    title_text="Acceleration",
    zeroline=True,
    zerolinewidth= 3
)
signalFig.update_layout(
    template = "plotly_white",
    paper_bgcolor = "white",
    plot_bgcolor = "white", 
)

processArea = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Tabs(
                                [
                                    dbc.Tab(trimTab, label="Trim"),
                                    dbc.Tab(detrendTab, label="Detrend"),
                                    dbc.Tab(filterTab, label="Filter"),
                                ],
                                className='nav-fill w-100'
                            ),
                        ], className="inputArea mx-2 mb-2 mt-1"),
                className="inputForm mx-2 mt-5 mb-4"),
            dbc.Button("Export Acceleration to Excel", id="exportAccButton", color="info", outline=True, className="mt-1 mx-2"),
        ], width=4),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=signalFig, id="signalFig"))
                ]),
            dbc.Row([
                html.Div(id='outputTable')
            ])
        ], width=8)
    ], className="")
)

defaultResponseFig = go.Figure()
defaultResponseFig.update_layout(
    title = 'Response Spectrum', title_x=0.5,
    template = "plotly_white",
    paper_bgcolor = "white",
    plot_bgcolor = "white", 
)
defaultResponseFig.update_xaxes(
    rangemode =  'tozero',
    title_text = 'Time (s)'
)
defaultResponseFig.update_yaxes(
    rangemode =  'tozero',
    title_text = 'Sa (g)'
)

# set the processing area
responseArea = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Label("Damping Ratio (%)", id="dampingLabel", className="mb-2 mt-1 mx-1"),
                            dbc.Input(type = "number", id='dampingRatioInput', value=5, className="mb-2 mt-1"),
                            dbc.Button("Create Response Spectrum", id="createResponse", color="primary", className="mt-2 w-100"),
                        ], className="inputArea mx-2 mb-2 mt-1"),
                className="inputForm mx-2 mt-5 mb-4"),
            dbc.Button("Export Response to Excel", id="exportResponseButton", color="info", outline=True, className="mt-1 mx-2"),
        ], width=3),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=defaultResponseFig, id="defaultResponseFig"))
                ]),
        ], width=9)
    ], className="")
)

# create arias intensity figure
defaultAriasFigure = go.Figure()
defaultAriasFigure.update_layout(
    title = 'Arias Intensity', title_x=0.5,
    template = "plotly_white",
    paper_bgcolor = "white",
    plot_bgcolor = "white", 
)
defaultAriasFigure.update_xaxes(
    rangemode =  'tozero',
    title_text = 'Time (s)'
)
defaultAriasFigure.update_yaxes(
    rangemode =  'tozero',
    title_text = 'Arias Intensity - Raw'
)

ariasArea = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Button("Create Arias Intensity", id="createArias", color="primary", className="mt-2 w-100"),
                        ], className="inputArea mx-2 mb-2 mt-1"),
                className="inputForm mx-2 mt-5 mb-4"),
        ], width=3),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=defaultAriasFigure, id="defaultAriasFigure"))
                ]),
        ], width=9)
    ], className="")
)

# create arias intensity figure
defaultFourierFig = go.Figure()
defaultFourierFig.update_layout(
    title = 'Fourier Transform', title_x=0.5,
    template = "plotly_white",
    paper_bgcolor = "white",
    plot_bgcolor = "white", 
    xaxis_type = 'log',
    yaxis_type = 'log'
)
defaultFourierFig.update_xaxes(
    rangemode =  'tozero',
    title_text = 'Frequency (Hz)'
)
defaultFourierFig.update_yaxes(
    rangemode =  'tozero',
    title_text = 'Fourier Amplitude'
)

fourierArea = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Button("Create Fourier Transform", id="createFourier", color="primary", className="mt-2 w-100"),
                        ], className="inputArea mx-2 mb-2 mt-1"),
                className="inputForm mx-2 mt-5 mb-4"),
        ], width=3),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div(dcc.Graph(figure=defaultFourierFig, id="defaultFourierFig"))
                ]),
        ], width=9)
    ], className="")
)

metaDict = {
    'col_1': ['Location', 'Date'],
    'col_2': ['No Data', 'No Data'],
}

defaultMetadata = pd.DataFrame(metaDict)

def generate_table(df):
    table_header = []
    table_body = []

    for index, row in df.iterrows():
        table_body.append(html.Tr([html.Td(row[col]) for col in df.columns]))

    return dbc.Table(
        table_header + table_body,
        bordered=True,
        style={'textAlign': 'center'}
    )

metadataArea = html.Div(
    dbc.Row([
        # input col
        dbc.Col([
            dbc.Card(
                html.Div(
                        children = [
                            dbc.Button("Get Metadata", id="getMetadata", color="primary", className="mt-2 w-100"),
                        ], className="inputArea mx-2 mb-2 mt-1"),
                className="inputForm mx-2 mt-5 mb-4")
        ], width=3),
        
        # graph col
        dbc.Col([
            dbc.Row([
                html.Div([generate_table(defaultMetadata)], id="metadataTable", className="mt-5")
                ]),
        ], width=9)
    ], className="")
)

data = [["response", "Response Spectrum"], ["arias", "Arias Intensity"], ["fourier", "Fourier Transform"], ["meta", "Metadata"]]
analysisArea = html.Div(
    [
        dmc.Tabs(
            [
                dmc.TabsList(
                    [
                        dmc.Tab("Response Spectrum", value="response"),
                        dmc.Tab("Arias Intensity", value="arias"),
                        dmc.Tab("Fourier Transform", value="fourier"),
                        dmc.Tab("Metadata", value="meta"),
                    ], grow=True
                ),
                dmc.TabsPanel(responseArea, value="response"),
                dmc.TabsPanel(ariasArea, value="arias"),
                dmc.TabsPanel(fourierArea, value="fourier"),
                dmc.TabsPanel(metadataArea, value="meta")
            ],
            value="response",
            orientation="horizontal"
        )
    ]
)

analysisDiv = dmc.MantineProvider(
    id='analysisDivMantine',
    theme={"colorScheme": "light"},
    children=[analysisArea]
)

operationsArea = html.Div([
    dbc.Container(
            dbc.Row(
                [
                    dbc.Col(html.Div(), width=1, className='h-100'),
                    dbc.Col(html.Div([dataImporter, uploadedFile, processArea, analysisDiv], className='h-100'), width=10),
                    dbc.Col(html.Div(), width=1, className='h-100'),
                ],
                className='h-100'
            ),
            fluid=True,
            className='h-100'
        )
])

def layout():
    return html.Div([
        navbar,
        processorTitle,
        operationsArea,
        dcc.Store(id='uploadedDataStore'),
        dcc.Download(id="downloadAcceleration"),
        dcc.Download(id="downloadResponse"),
    ])

# upload file check
@callback(
    Output('outputFileName', 'children'),
    Output('uploadedDataStore', 'data'),
    Input('uploadData', 'contents'),
    Input('uploadData', 'filename'),
)
def filenameOutput(contents, filename):
    if contents is None:
        return html.Div(), None
    
    if any(filename.endswith(ext) for ext in ['asc', 'AT2']):
        return html.Div([
            f"✅ File succesfully uploaded: {filename}"
        ], className="mt-4"), contents
    else:
        return html.Div([
            "❗File format is not supported. Supported formats: AT2, ASC"
        ], className="mt-4"), contents

# visualize the uploaded data
@callback(
    Output('signalFig', 'figure'),
    Input('uploadedDataStore', 'data'),
    Input('uploadData', 'filename'),
    State('signalFig', 'figure'),
)
def visualizeData(contents, filename, fig):
    if contents is None:
        return fig
    
    # clean fig
    fig['data'] = []
    
    # visualize at2 data
    if filename.endswith('AT2'):
        at2Object = AT2(contents)
        at2Frame = at2Object.accdata()
        at2Trace = go.Scatter(
                x = at2Frame['Time (s)'],
                y = at2Frame['Acceleration (g)'],
                line=dict(color="blue")
            )
        fig['data'].append(at2Trace)
        fig['layout'].update(
            xaxis=dict(title='Time (s)'),
            yaxis=dict(title='Acceleration (g)')
        )
    
    # visualize asc data
    elif filename.endswith('asc'):
        ascObject = ASC(contents)
        ascFrame = ascObject.accdata()
        ascTrace = go.Scatter(
            x = ascFrame['Time (s)'],
            y = ascFrame['Acceleration (cm/s^2)'],
            line=dict(color="blue")
        )
        fig['data'].append(ascTrace)
        fig['layout'].update(
            xaxis=dict(title='Time (s)'),
            yaxis=dict(title='Acceleration (cm/s^2)')
        )
        
    return fig

# update trim input
@callback(
    [
        Output('trimRangeInput', 'min'),
        Output('trimRangeInput', 'max'),
        Output('trimRangeInput', 'value'),
        Output('trimRangeInput', 'marks'),
    ],
    
    [
        Input('uploadedDataStore', 'data'),
        Input('uploadData', 'filename')
    ]
)
def updateInput(contents, filename):
    if contents is None:
        raise PreventUpdate
        
    # get at2 data
    if filename.endswith('AT2'):
        at2Object = AT2(contents)
        at2Frame = at2Object.accdata()
        timeMin = at2Frame['Time (s)'].to_list()[0]
        timeMax = at2Frame['Time (s)'].to_list()[-1]
        
        return timeMin, timeMax, [timeMin, timeMax], [{"value": timeMin, "label": str(timeMin)}, {"value": timeMax, "label": str(timeMax)}]
        
    # get asc data
    elif filename.endswith('asc'):
        ascObject = ASC(contents)
        ascFrame = ascObject.accdata()
        timeMin = ascFrame['Time (s)'].to_list()[0]
        timeMax = ascFrame['Time (s)'].to_list()[-1]
        
        return timeMin, timeMax, [timeMin, timeMax], [{"value": timeMin, "label": str(timeMin)}, {"value": timeMax, "label": str(timeMax)}]

# apply trim
@callback(
    Output('signalFig', 'figure', allow_duplicate=True),
    [
        State('trimRangeInput', 'value'),
        State('signalFig', 'figure'),
        State('uploadedDataStore', 'data'),
        State('uploadData', 'filename'),        
    ],
    Input('applyTrim', 'n_clicks'),
    Input('resetTrim', 'n_clicks'),
    prevent_initial_call=True
)
def applyTrim(trimRange, fig, contents, filename, clickApply, clickReset):
    if not clickApply and not clickReset:
        raise PreventUpdate
    
    # Determine which button was clicked
    triggered_id = ctx.triggered_id
    
     # line color
    lineColor = 'blue'

    # get at2 data
    if filename.endswith('AT2'):
        at2Object = AT2(contents)
        at2Frame = at2Object.accdata()
        originalData = pd.DataFrame({'x': at2Frame['Time (s)'].to_list(), 'y': at2Frame['Acceleration (g)'].to_list()})
        
    # get asc data
    elif filename.endswith('asc'):
        ascObject = ASC(contents)
        ascFrame = ascObject.accdata()
        originalData = pd.DataFrame({'x': ascFrame['Time (s)'].to_list(), 'y': ascFrame['Acceleration (cm/s^2)'].to_list()})
        

    if triggered_id == 'applyTrim':
        
        # trim the data
        trimmedData = originalData[(originalData['x'] >= trimRange[0]) & (originalData['x'] <= trimRange[1])]
        trimmedScatter = go.Scatter(
            x=trimmedData['x'],
            y=trimmedData['y'],
            line=dict(color=lineColor)
        )
        
        # clean the fig
        fig['data'] = []
        
        # add the new data
        fig['data'].append(trimmedScatter)
    
    elif triggered_id == 'resetTrim':
        originalScatter = go.Scatter(
            x=originalData['x'],
            y=originalData['y'],
            line=dict(color=lineColor)
        )
        
        # clean the fig
        fig['data'] = []
        
        # add the original data back
        fig['data'].append(originalScatter)
    
    return fig

# input detrend update
@callback(
    Output('orderInput', 'style'),
    Output('orderLabel', 'style'),
    Input('detrendInput', 'value')
)
def showOrder(detrendMethod):
    if detrendMethod == 'Linear':
        return {'display': 'none'}, {'display': 'none'}

    elif detrendMethod == 'Polynomial':
        return {'display': 'block'}, {'display': 'block'}
    
# detrend function
@callback(
    Output('signalFig', 'figure', allow_duplicate=True),
    State('detrendInput', 'value'),
    State('orderInput', 'value'),
    State('signalFig', 'figure'),
    Input('applyDetrend', 'n_clicks'),
    prevent_initial_call=True
)
def applyDetrend(method, order, fig, n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    # line color
    lineColor = 'blue'

    # get current data
    current_data = pd.DataFrame({'Time (s)': fig['data'][0]['x'], 'Acceleration': fig['data'][0]['y']})

    # Apply detrending
    detrended_data = detrendFunction(current_data, method=method.lower(), order=order)

    detrended_scatter = go.Scatter(
        x=detrended_data['Time (s)'],
        y=detrended_data['Detrended Acceleration'],
        line=dict(color=lineColor)
    )

    # Update the figure
    fig['data'] = []
    fig['data'].append(detrended_scatter)

    return fig

# filter input area update
@callback(
    Output('lowPassLabel', 'style'),
    Output('lowPassInput', 'style'),
    Output('highPassLabel', 'style'),
    Output('highPassInput', 'style'),
    Input('filterMethodInput', 'value')
)
def updateInputArea(method):
    if method == 'Band-Pass':
        return {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}
    elif method == 'High-Pass':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}, {'display': 'block'}
    elif method == 'Low-Pass':
        return {'display': 'block'}, {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    
# apply filter
@callback(
    Output('signalFig', 'figure', allow_duplicate=True),
    Input('applyFilter', 'n_clicks'),
    State('filterMethodInput', 'value'),
    State('lowPassInput', 'value'),
    State('highPassInput', 'value'),
    State('filterOrderInput', 'value'),
    State('signalFig', 'figure'),
    prevent_initial_call = True
)
def applyFilter(click, filterMethod, lowpasscorner, highpasscorner, filterOrder, fig):
    
    if click is None:
        raise PreventUpdate
    
    # line color
    lineColor = 'blue'

    # get the data
    current_data = pd.DataFrame({'x': fig['data'][0]['x'], 'y': fig['data'][0]['y']})
    
    # get the delta
    delta = current_data['x'][1] - current_data['x'][0]
    
    # filter the data
    if filterMethod == 'Band-Pass':
        filteredData = filterFunction(current_data, 'bandpass', [lowpasscorner, highpasscorner], delta, filterOrder)
    elif filterMethod == 'Low-Pass':
        filteredData = filterFunction(current_data, 'lowpass', [lowpasscorner], delta, filterOrder)
    elif filterMethod == 'High-Pass':
        filteredData = filterFunction(current_data, 'highpass', [highpasscorner], delta, filterOrder)        
    
    # create scatter
    filteredScatter = go.Scatter(
        x = filteredData['x'],
        y = filteredData['y'],
        line=dict(color=lineColor)
    )
    
    # clean the fig
    fig['data'] = []
    
    # visualize
    fig['data'].append(filteredScatter)
    
    return fig

# create response spectrum
@callback(
    Output('defaultResponseFig', 'figure'),
    [
        State('signalFig', 'figure'),
        State('defaultResponseFig', 'figure'),
        State('dampingRatioInput', 'value'),
    ],
    Input('createResponse', 'n_clicks')
)
def createResponseSpectrum(signalFig, responseFig, dampingRatio, click):
    if click is None:
        raise PreventUpdate
    
    # line color
    lineColor = 'blue'

    # get the current data
    accData = pd.DataFrame({'x': signalFig['data'][0]['x'], 'y': signalFig['data'][0]['y']})
    
    # get the delta
    delta = accData['x'][1] - accData['x'][0]
    
    dampingRatio = dampingRatio/100
    
    response = ResponseSpectrum(accData['x'].to_list(), accData['y'].to_list(), dampingRatio, delta)
    
    responseFrame = pd.DataFrame({'x': signalFig['data'][0]['x'], 'y': response})
    
    # create scatter
    responseScatter = go.Scatter(
        x = responseFrame['x'],
        y = responseFrame['y'],
        line=dict(color=lineColor)
    )
    
    # clean the fig
    responseFig['data'] = []
    
    # visualize
    responseFig['data'].append(responseScatter)
    
    return responseFig

@callback(
    Output('defaultAriasFigure', 'figure'),
    [
        State('signalFig', 'figure'),
        State('defaultAriasFigure', 'figure'),
    ],
    Input('createArias', 'n_clicks')
)
def createAriasFigure(signalFig, ariasFig, click):
    if click is None:
        raise PreventUpdate
    
    # line color
    lineColor = 'blue'
    
    # get the data     
    accData = pd.DataFrame({'x': signalFig['data'][0]['x'], 'y': signalFig['data'][0]['y']})
    
    # get the sample
    sample = accData['x'][1] - accData['x'][0]
    
    # get the arias dict
    ariasDict = ariasIntensityCreator(accData['y'].to_list(), sample)
        
    # clean the fig
    ariasFig['data'] = []
    ariasFig['layout']['shapes'] = []
    ariasFig['layout']['annotations'] = []

    # create arias scatter
    ariasScatter = go.Scatter(
        name='Arias Intensity',
        x = ariasDict['ariasTime'],
        y = ariasDict['ariasIntensity'],
        line=dict(color=lineColor)
    )
    
    # add scatter to the figure
    ariasFig['data'].append(ariasScatter)
    
    # create significant duration shape
    startTime = ariasDict['ariasTime'][ariasDict['timeAriasList'][0]]
    endTime = ariasDict['ariasTime'][ariasDict['timeAriasList'][-1]]
    
    shape = {
        'type': 'rect',
        'x0': startTime,
        'y0': 0,
        'x1': endTime,
        'y1': max(ariasDict['ariasIntensity']),
        'fillcolor': 'Red',
        'opacity': 0.2,
        'name': 'Significant Duration',
        'line': {
            'color': 'Red'
        },
    }
    
    # add shape to the figure's layout
    if 'shapes' not in ariasFig['layout']:
        ariasFig['layout']['shapes'] = []
    
    ariasFig['layout']['shapes'].append(shape)
    
    significantDuration = round(float(ariasDict['durationAriasIntensity']), 2)
    # add text
    annotation = {
        'x': (endTime-startTime) - (endTime-startTime)/3,
        'y': max(ariasDict['ariasIntensity']) + sample,
        'xref': 'x',
        'yref': 'y',
        'text': f'Significant Duration: {significantDuration} sec',
        'showarrow': False,
        'font': {
            'size': 12,
            'color': 'black'
        },
        'align': 'center'
    }
    
    # add annotation to the figure's layout
    if 'annotations' not in ariasFig['layout']:
        ariasFig['layout']['annotations'] = []
    
    ariasFig['layout']['annotations'].append(annotation)
    
    # add lines for 5% and 95%
    line_5 = {
        'type': 'line',
        'x0': 0,
        'y0': ariasDict['arias05'],
        'x1': max(ariasDict['ariasTime']),
        'y1': ariasDict['arias05'],
        'line': {
            'color': 'gray',
            'width': 1,
            'dash': 'dot'
        },
        'name': '5%'
    }
    
    line_95 = {
        'type': 'line',
        'x0': 0,
        'y0': ariasDict['arias95'],
        'x1': max(ariasDict['ariasTime']),
        'y1': ariasDict['arias95'],
        'line': {
            'color': 'gray',
            'width': 1,
            'dash': 'dot'
        },
        'name': '95%'
    }
    
    ariasFig['layout']['shapes'].append(line_5)
    ariasFig['layout']['shapes'].append(line_95)
    
    # Add annotations for 5% and 95% lines
    annotation_5 = {
        'x': max(ariasDict['ariasTime']),
        'y': ariasDict['arias05'],
        'xref': 'x',
        'yref': 'y',
        'text': '5%',
        'showarrow': False,
        'font': {
            'size': 12,
            'color': 'gray'
        },
        'align': 'right'
    }
    
    annotation_95 = {
        'x': max(ariasDict['ariasTime']),
        'y': ariasDict['arias95'],
        'xref': 'x',
        'yref': 'y',
        'text': '95%',
        'showarrow': False,
        'font': {
            'size': 12,
            'color': 'gray'
        },
        'align': 'right'
    }
    
    ariasFig['layout']['annotations'].append(annotation_5)
    ariasFig['layout']['annotations'].append(annotation_95)

    return ariasFig

@callback(
    Output('defaultFourierFig', 'figure'),
    [
        State('signalFig', 'figure'),
        State('defaultFourierFig', 'figure'),
    ],
    Input('createFourier', 'n_clicks')
)
def createFourierFigure(signalFig, fourierFig, click):
    if click is None:
        raise PreventUpdate
    
    # line color
    lineColor = 'blue'
    
    # get the data     
    accData = pd.DataFrame({'x': signalFig['data'][0]['x'], 'y': signalFig['data'][0]['y']})
    
    # get the sample
    sample = accData['x'][1] - accData['x'][0]
    
    # perform fourier transform
    freq, amp = fourierTransform(accData['y'].to_list(), sample, len(accData['y'].to_list()))
    
    # clean the fig
    fourierFig['data'] = []
    
    fourierTrace = go.Scatter(
        x = freq,
        y = amp,
        line=dict(color = lineColor)
    )
    
    # add trace to the fig
    fourierFig['data'].append(fourierTrace)
    
    return fourierFig

# update metadata
@callback(
    Output('metadataTable', 'children'),
    State('uploadedDataStore', 'data'),
    State('uploadData', 'filename'),
    State('metadataTable', 'figure'),
    Input('getMetadata', 'n_clicks')
)
def getMetadata(contents, filename, table, click):
    if contents is None:
        raise PreventUpdate
    
    # create metadata table for at2
    if filename.endswith('AT2'):
        at2Object = AT2(contents)
        upMetadata = at2Object.metadata()
        
        metadatadict = {
                'col_1': ['Location', 'Date', 'Orientation'],
                'col_2': [upMetadata[0], upMetadata[1], upMetadata[2]],
            }
        metadataframe = pd.DataFrame(metadatadict)
        
        return generate_table(metadataframe)
        
    # create metadata table for at2
    elif filename.endswith('asc'):
        ascObject = ASC(contents)
        upMetadata = ascObject.metadata()
        
        keys, values = [], []
        
        for key, value in upMetadata.items():
            keys.append(key)
            values.append(value)
        
        metadatadict = {
                'col_1': keys,
                'col_2': values,
            }
        
        metadataframe = pd.DataFrame(metadatadict)
        
        return generate_table(metadataframe)

# export acceleration to excel function
@callback(
    Output('downloadAcceleration', 'data'),
    Input('exportAccButton', 'n_clicks'),
    State('signalFig', 'figure'),
    prevent_initial_call = True
)
def downloadAcceleration(click, fig):
    if fig and fig['data']:
        accData = fig['data'][0]
        time = accData['x']
        acc = accData['y']
        accFrame = pd.DataFrame({'Time': time, 'Acceleration': acc})
    else:
        accFrame = pd.DataFrame(columns=['Time', 'Acceleration'])
        
    return dcc.send_data_frame(accFrame.to_excel, "exportedAcceleration.xlsx", sheet_name="Sheet1", index=False)

# export response to excel function
@callback(
    Output('downloadResponse', 'data'),
    Input('exportResponseButton', 'n_clicks'),
    State('defaultResponseFig', 'figure'),
    prevent_initial_call = True
)
def downloadResponse(click, fig):
    if fig and fig['data']:
        responseData = fig['data'][0]
        time = responseData['x']
        sa = responseData['y']
        responseFrame = pd.DataFrame({'Time': time, 'Sa': sa})
    else:
        responseFrame = pd.DataFrame(columns=['Time', 'Sa'])
        
    return dcc.send_data_frame(responseFrame.to_excel, "exportedResponseSpectrum.xlsx", sheet_name="Sheet1", index=False)