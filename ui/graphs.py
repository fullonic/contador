import plotly.graph_objects as go
from functools import lru_cache
import time

# import plotly.express as px
from plotly.subplots import make_subplots
from plotly.offline import plot


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
    fig: go = make_subplots(specs=[[{"secondary_y": True}]])
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
    # plot_div = plot(fig, output_type="div", include_plotlyjs=False)
    fig.update_layout(
        title=f"Usuario: {dni}",
        autosize=True,
        margin=dict(l=50, r=50, b=10, t=50, pad=1),
    )
    fig.write_html("ui/templates/_user_graph.html", include_plotlyjs="cdn")
    return "_user_graph.html"


def create_plot(dni: str, data: list):
    start = time.perf_counter()
    dni, axis = generate_graphic_axis(dni, data)
    plot_ = generate_graphic(dni, axis)
    print("total", time.perf_counter() - start)
    return plot_


def _generate_barchart(x_axis, datasets=[], cfg={}):
    data = [
        go.Bar(name=ds["name"], x=x_axis, y=ds["values"], marker={"color":ds["color"]})
        for ds in datasets
    ]
    fig = go.Figure(data=data)
    fig.update_layout(barmode="group", **cfg)
    fig.write_html("ui/templates/_user_graph.html", include_plotlyjs="cdn")
    return True


def create_barchart(user_dni, data):
    x_axis = [f"week {d['week']}, {d['month']}, {d['year']} " for d in data]
    ds1 = {"name": "punta", "color": "red", "values": [d["max_punta"] for d in data]}
    ds2 = {"name": "llana", "color": "orange", "values": [d["max_llana"] for d in data]}
    ds3 = {"name": "valle", "color": "green", "values": [d["max_valle"] for d in data]}
    cfg = {
        "title": f"Usuario {user_dni}",
        "autosize": True,
        "margin": dict(l=50, r=50, b=10, t=50, pad=1),
    }
    barchart = _generate_barchart(x_axis=x_axis, datasets=[ds1, ds2, ds3], cfg=cfg)
