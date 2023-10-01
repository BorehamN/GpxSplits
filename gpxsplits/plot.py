import plotly.graph_objects as go
import plotly.express as px

def draw_course(course, gpx_df=None):
    fig = go.Figure()

    # Add GPX trace
    if not gpx_df is None:
        fig.add_trace(go.Scattermapbox(
            mode = "markers+lines",
            lon = gpx_df['lon'],
            lat = gpx_df['lat'],
            name='GPX traces')
        )

    # Add Course Gate
    for gate in course['course']:
        lons = [gate['left'][0], gate['right'][0]]
        lats = [gate['left'][1], gate['right'][1]]
        fig.add_trace(go.Scattermapbox(
            mode = "markers+lines",
            lon = lons,
            lat = lats,
            #color='red',
            name = gate['name']))
    
    # TODO: Move from gpx_df lat, lon to course gates
    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        mapbox = {
            'style': "stamen-terrain",
            'center': {'lon': gpx_df['lon'].mean(), 'lat': gpx_df['lat'].mean()},
            'zoom': 13
        })
    
    return fig


def visualise_normalised_splits(course, norm_splits):
    vis_df = norm_splits.reset_index().melt(id_vars='lap')
    fig = px.line(vis_df, x='gate', y='value', color='lap',
            title=f"{course['name']} Normalised Splits")