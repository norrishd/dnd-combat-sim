"""Web app to visualise an encounter."""

import random
from typing import Optional

from dash import Dash, Input, Output, State, callback, ctx, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from dnd_combat_sim.creature import Creature
from dnd_combat_sim.encounter import Encounter1v1
from dnd_combat_sim.utils import MONSTERS

MONSTER_OPTS = MONSTERS.index.to_list()

print("Re-re-reloooad!")

# TODO make everything JSON-serializable and store this using dcc.Store for session-safe state
encounter = Encounter1v1()


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

combat_controls = dbc.Col([dbc.Row(dbc.Button("Roll initiative")), dbc.Row(dbc.Button("Attack!"))])

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("D&D Combat Sim"))),  # width={"size": 6, "offset": 3})),
        dbc.Row([dbc.Col(dcc.Dropdown(MONSTER_OPTS, id="monster-selection"))]),
        dbc.Row([dbc.Col(dcc.Graph(id="graph-content"), xs=10), combat_controls]),
        dbc.Row(dbc.Col(html.Div(id="logs"))),
    ]
)


@callback(
    [Output("graph-content", "figure"), Output("logs", "children")],
    [Input("monster-selection", "value")],
    State("logs", "children"),
)
def update_graph(monster_name: Optional[str], logs: str):
    """Create monsters."""
    global encounter

    print(monster_name)

    if monster_name is None or encounter.creatures[1] is not None:
        return no_update

    start_x = 0 if encounter.creatures[0] is None else 100
    monster = Creature.init(monster_name, start_x=start_x)
    if not logs:
        logs = []
    else:
        logs = [logs]
    logs.append(f"Added {monster.name} to the encounter.")

    encounter.add_creature(monster)

    monster_coords = []

    for monster, color in zip(encounter.creatures, ["green", "red"]):
        if monster is None:
            continue
        monster_coords.append(
            {
                "monster": monster.name,
                "x": monster.position.x,
                "y": monster.position.y,
                "team": f"{color.title()} Team",
                "color": color,
            }
        )
    df = pd.DataFrame(monster_coords)
    layout = go.Layout(
        xaxis=dict(dtick=5, range=[-5, 105], showgrid=True, tick0=5, showticklabels=False),
        yaxis=dict(dtick=5, range=[-20, 20], showgrid=True, tick0=5, showticklabels=False),
        margin=dict(l=20, r=20, t=40, b=40),
    )
    if df.empty:
        df = pd.DataFrame(columns=["monster", "x", "y", "team", "color"])

    data = go.Scatter(
        x=df["x"],
        y=df["y"],
        hoverinfo="x+y+text",
        name="monster",
        text=df["monster"].to_list(),
        mode="markers",
        marker=dict(color=df["color"], size=50),
    )
    return go.Figure(data=data, layout=layout), [
        html.Span(line, style={"display": "block"}) for line in logs
    ]
