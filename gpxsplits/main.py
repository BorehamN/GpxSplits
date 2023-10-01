import os
import click
import glob
import pandas as pd

import core
import plot

click.command()
click.argument('corsefile', nargs=1)
click.argument('filepaths', nargs=-1)
def gpxsplits(coursefile, filepaths):
    course = core.import_course(coursefile)
    filepaths = [glob.glob(i) for i in filepaths]

    all_split_times = []
    for gpx_file in filepaths:
        gpx_file_name, ext = os.path.splitext(os.path.basename(gpx_file))
        gpx_data = core.import_gpx(gpx_file)
        gate_times = core.find_gate_times(course, gpx_data)
        split_times = core.gate_times_to_splits(course, gate_times)
        split_times['ID'] = gpx_file_name
        all_split_times.append(split_times)

    splits = pd.concat(all_split_times)
