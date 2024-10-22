from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from applications.asce import asceApp
from applications.tbec import tbecApp
from applications.seisscale import seisscaleApp
from applications.eqprocess import processorApp

app = Dash(__name__, suppress_callback_exceptions=True, title="SeisKit", external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    dcc.Location(id='redirect', refresh=True),
    html.Div(id='page-content'),
])

@callback(
    Output('redirect', 'href', allow_duplicate=True),
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def display_page(pathname):
    if pathname in ['/', '/home']:
        return 'https://seiskit.com/applications', None
    elif pathname == '/tbecapp':
        content = tbecApp.layout()
    elif pathname == '/asceapp':
        content = asceApp.layout()
    elif pathname == '/eqprocessor':
        content = processorApp.layout()
    elif pathname == '/seisscale':
        content = seisscaleApp.layout()
    else:
        content = '404 Page Not Found'
    
    return None, html.Div(content)

if __name__ == '__main__':
    app.run_server(debug=True)
