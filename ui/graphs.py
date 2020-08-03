import plotly.graph_objects as go
from functools import lru_cache
import time

# import plotly.express as px
from plotly.subplots import make_subplots


def generate_graphic_axis(dni: str, data: list):
    x_axis_time, y_axis_power, y2_axis_percent = [], [], []
    for row in data:
        x_axis_time.append(row.date)
        y_axis_power.append(row.instantaneous_consume)
        y2_axis_percent.append(row.percent)
    return (dni, (tuple(x_axis_time), tuple(y_axis_power), tuple(y2_axis_percent)))


def generate_graphic(dni: str, axis: tuple):
    x, y, y2 = axis
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=x, y=y, name=dni, line={"color": "green", "width": 1}, showlegend=True,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y2,
            name="Percent",
            line={"color": "red", "width": 1},
            showlegend=True,
        ),
        secondary_y=True,
    )
    return fig.to_html()


def create_plot(dni: str, data: list):
    start = time.perf_counter()
    dni, axis = generate_graphic_axis(dni, data)
    plot = generate_graphic(dni, axis)
    print("total", time.perf_counter() - start)
    return plot
