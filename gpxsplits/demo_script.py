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

def calc_azimuth(line):
    xs = line.coords.xy[0]
    ys = line.coords.xy[1]
    azimuth = np.arctan2(xs[0]-xs[1], ys[0]-ys[1])
    return azimuth

def get_intecept_angle(line1, line2):
    azi1 = calc_azimuth(line1)
    azi2 = calc_azimuth(line2)
    angle = np.rad2deg(azi2-azi1)
    return angle

def check_intersept(seg, gate):
    angle = np.NAN
    line_gate = LineString([gate['left'], gate['right']])
    line_gpx  = LineString([seg.iloc[0][['lon', 'lat']].values, seg.iloc[1][['lon', 'lat']].values])
    int_pt = line_gpx.intersection(line_gate)
    if int_pt:
        angle = get_intecept_angle(line_gpx, line_gate)
        if angle < 0 or angle > 180:
            int_pt = False
    #return int_pt.x, int_pt.y
    return int_pt, angle

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
        (point, angle) = check_intersept(seg, gate)
        # Get time
        if point:
            intersection_time = get_intersection_time(point, seg)
            print(point, intersection_time, seg.index)
            splits.append({
                "gate": gate["name"],
                "epoch": intersection_time,
                "idx": idx,
                "angle": angle
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

# %% Normalise splits
import plotly.express as px

avg_split_time = splits2.dropna().mean()

# splits3 = splits2.diff(axis=1).fillna(pd.Timedelta(0)) + avg_split_time
# vis_df = splits3.reset_index().melt(id_vars='lap')

norm_splits = []
laps = []
for lap, split in splits2.iterrows():
    offset_time = avg_split_time[~split.isna().values][0]
    norm_split = split + offset_time - avg_split_time
    norm_splits.append(norm_split.dt.total_seconds())
    laps.append(lap)

norm_splits = pd.DataFrame(norm_splits)
norm_splits.index = laps
norm_splits.index.name = 'lap'

vis_df = norm_splits.reset_index().melt(id_vars='lap')
px.line(vis_df, x='gate', y='value', color='lap')

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
