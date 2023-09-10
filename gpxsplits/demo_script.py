# %%s
import xml.etree.ElementTree as ET
import pandas as pd

gpx_file_path = r"C:\Users\nickb\Documents\GpxSplits\GpxSplits\data\Lipno_Classic_1.gpx"

tree = ET.parse(gpx_file_path)
root = tree.getroot()
track_points = [i for i in root.findall('./*/*/*') if i.tag.endswith('trkpt')]
# %%

def handle_missing(node):
    if not node is None:
        return node.text
    else:
        return ''

df = pd.DataFrame([i.attrib for i in track_points])
df['elev'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}ele')) for i in track_points]
df['epoch'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}time')) for i in track_points]
df['temp'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}atemp')) for i in track_points]
df['hr'] = [handle_missing(i.find('{http://www.topografix.com/GPX/1/1}extensions/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}TrackPointExtension/{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')) for i in track_points]
# %%
