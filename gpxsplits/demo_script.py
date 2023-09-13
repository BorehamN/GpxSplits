# %%s
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import json

gpx_file_path = r"C:\Users\nickb\Documents\GpxSplits\GpxSplits\data\Lipno_practice_1.gpx"
course_file = r"C:\Users\nickb\Documents\GpxSplits\GpxSplits\data\Lipno_splits.json"

with open(course_file) as fp:
    course = json.loads(fp.read())

tree = ET.parse(gpx_file_path)
root = tree.getroot()
track_points = [i for i in root.findall('./*/*/*') if i.tag.endswith('trkpt')]
# %%

def handle_missing(node):
    if not node is None:
        node_text = node.text.strip()
        try:
            return float(node_text)
        except:
            return pd.Timestamp(node_text)
    else:
        return np.NaN

df = pd.DataFrame([i.attrib for i in track_points])
df['lat'] = df['lat'].apply(float)
df['lon'] = df['lon'].apply(float)
df['elev'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}ele')) for i in track_points]
df['epoch'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}time')) for i in track_points]
df['temp'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')) for i in track_points]
df['hr'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')) for i in track_points]

# %%
from shapely.geometry import LineString, Point


def check_intersept(seg, gate):
    line_gate = LineString([gate['left'], gate['right']])
    line_gpx  = LineString([seg.iloc[0][['lon', 'lat']].values, seg.iloc[1][['lon', 'lat']].values])
    int_pt = line_gpx.intersection(line_gate)
    #return int_pt.x, int_pt.y
    return int_pt

def get_intersection_time(point, seg):
    seg_diff = seg.diff().iloc[1]
    seg_length = np.sqrt((seg_diff[['lat', 'lon']].values**2).sum())
    point_diff = np.array([seg.iloc[0]['lon'] - point.x, seg.iloc[0]['lat'] - point.y])
    point_length = np.sqrt((point_diff**2).sum())
    fractional_diff = point_length/seg_length
    delta_t = seg_diff['epoch'] * fractional_diff
    intersect_time = seg['epoch'].iloc[0] + delta_t
    return intersect_time

splits = []
for seg in df.rolling(window=2, min_periods=2):
    if len(seg) < 2:
        continue

    for idx, gate in enumerate(course['course']):
        point = check_intersept(seg, gate)
        # Get time
        if point:
            intersection_time = get_intersection_time(point, seg)
            print(point, intersection_time, seg.index)
            splits.append({
                "gate": gate["name"],
                "epoch": intersection_time,
                "idx": idx
            })

splits = pd.DataFrame(splits)

# %%
# Order splits by time
# Count number of intercepts for each gate

splits['lap'] = (splits['idx'].diff() < 1).cumsum() + 1

elapsed = splits[['lap', 'epoch']].groupby('lap').apply(lambda x: x - x.iloc[0])

splits['elapsed'] = elapsed['epoch']

splits2 = splits.pivot(columns='gate', index='lap', values='elapsed')
splits2 = splits2[[g['name'] for g in course['course']]]

# %% Visualise Course

import plotly.graph_objects as go

fig = go.Figure(go.Scattermapbox(
    mode = "markers+lines",
    lon = df['lon'],
    lat = df['lat'],
    name='GPX traces'))

for gate in course['course']:
    lons = [gate['left'][0], gate['right'][0]]
    lats = [gate['left'][1], gate['right'][1]]
    fig.add_trace(go.Scattermapbox(
        mode = "markers+lines",
        lon = lons,
        lat = lats,
        #color='red',
        name = gate['name']))


fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'style': "stamen-terrain",
        'center': {'lon': df['lon'].mean(), 'lat': df['lat'].mean()},
        'zoom': 13
    })

# fig.add_trace(go.Scattermapbox(
#         mode = "markers+lines",
#         lon = [point[0]],
#         lat = [point[1]],
#         name = 'intercept'))

fig.show()
# %%
