from dash_leaflet import express as dlx 
from matplotlib.colorbar import Colorbar
import numpy as np


def create_colorscale(color1 : str, color2 : str, n_colors : int)->list:
    color1_ = [int(i) for i in color1[4:-1].split(",")]
    color2_ = [int(i) for i in color2[4:-1].split(",")]
    colors_ = np.linspace(start=color1_, stop=color2_, num=n_colors)
    colors  = [str(f"rgb{int(i[0]), int(i[1]), int(i[2])}") for i in colors_]
    return colors

def CategoricalColorbar(colorscale : list|str, classes : list, width : int, height : int, position : str = "bottomright",**kwargs)->Colorbar:
    ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+km".format(classes[-1])]
    colorbar = dlx.categorical_colorbar(ctg, colorscale, width, height, position,**kwargs)
    