import xml.etree.ElementTree as ET
import json

import pandas as pd
import numpy as np
from shapely.geometry import LineString, Point

def handle_missing(node):
    if not node is None:
        node_text = node.text.strip()
        try:
            return float(node_text)
        except:
            return pd.Timestamp(node_text)
    else:
        return np.NaN
    

def import_gpx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    track_points = [i for i in root.findall('./*/*/*') if i.tag.endswith('trkpt')]

    df = pd.DataFrame([i.attrib for i in track_points])
    df['lat'] = df['lat'].apply(float)
    df['lon'] = df['lon'].apply(float)
    df['elev'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}ele')) for i in track_points]
    df['epoch'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}time')) for i in track_points]
    df['temp'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')) for i in track_points]
    df['hr'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')) for i in track_points]

    return df


def import_course(file_path):
    with open(file_path) as fp:
        course = json.loads(fp.read())

    return course


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


def find_gate_times(course, gpx_df):
    gate_times = []
    for seg in gpx_df.rolling(window=2, min_periods=2):
        if len(seg) < 2:
            continue

        for idx, gate in enumerate(course['course']):
            (point, angle) = check_intersept(seg, gate)
            # Get time
            if point:
                intersection_time = get_intersection_time(point, seg)
                print(point, intersection_time, seg.index)
                gate_times.append({
                    "gate": gate["name"],
                    "epoch": intersection_time,
                    "idx": idx,
                    "angle": angle
                })

    gate_times = pd.DataFrame(gate_times)
    return gate_times


def to_total_seconds(x):
    try:
        return x.dt.total_seconds()
    except:
        return x


def gate_times_to_splits(id_str, course, gate_times):
    gate_times['lap'] = (gate_times['idx'].diff() < 1).cumsum() + 1
    gate_times['lap'] = gate_times['lap'].apply(lambda x: f"{id_str} {x}")
    elapsed = gate_times[['lap', 'epoch']].groupby('lap').apply(lambda x: x - x.iloc[0])
    gate_times['elapsed'] = elapsed['epoch']

    splits2 = gate_times.pivot(columns='gate', index='lap', values='elapsed')
    splits2 = splits2[[g['name'] for g in course['course']]]
    splits2 = splits2.apply(lambda x: to_total_seconds(x))
    return splits2

def normalise_splits(splits):
    avg_split_time = splits.dropna().mean()

    norm_splits = []
    laps = []
    for lap, split in splits.iterrows():
        offset_time = avg_split_time[~split.isna().values][0]
        norm_split = split + offset_time - avg_split_time
        #norm_splits.append(norm_split.dt.total_seconds())
        norm_splits.append(norm_split)
        laps.append(lap)

    norm_splits = pd.DataFrame(norm_splits)
    norm_splits.index = laps
    norm_splits.index.name = 'lap'
    return norm_splits