import plotly.graph_objects as go

def overlay_interactions(fig, interactions, layer_name, color):
    """
    Adds overlays for interactions in visualizations.
    """
    for interaction in interactions:
        fig.add_trace(
            go.Scatter3d(
                x=interaction["x"],
                y=interaction["y"],
                z=interaction["z"],
                mode="lines",
                line=dict(color=color, width=2),
                name=layer_name
            )
        )
    return fig

def generate_heatmap(data, xaxis, yaxis, zaxis, title):
    """
    Generates a heatmap for scalar fields (e.g., energy density).
    """
    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=xaxis,
        y=yaxis,
        colorscale="Viridis"
    ))
    fig.update_layout(
        title=title,
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig
