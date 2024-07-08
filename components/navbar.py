import dash_bootstrap_components as dbc
from dash import html

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Go To Applications", href="https://seiskit.com/applications")),
    ],
    brand=html.Img(src="/assets/static/logoNew.png", height="22px"),
    brand_href="https://seiskit.com/",
    color="white",
    dark=False,
    style={
        'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
        'height': '80px'
    }
)