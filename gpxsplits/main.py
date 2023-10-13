import os
import glob

import click
import pandas as pd

from . import core
from . import plot

@click.command()
@click.argument('output', nargs=1)
@click.argument('coursefile', nargs=1)
@click.argument('filepaths', nargs=-1)
def gpxsplits(output, coursefile, filepaths):
    "Help String"
    course = core.import_course(coursefile)
    filepaths = [j for i in filepaths for j in glob.glob(i)]

    all_split_times = []
    for gpx_file in filepaths:
        gpx_file_name, ext = os.path.splitext(os.path.basename(gpx_file))
        gpx_data = core.import_gpx(gpx_file)
        gate_times = core.find_gate_times(course, gpx_data)
        split_times = core.gate_times_to_splits(gpx_file_name, course, gate_times)
        all_split_times.append(split_times)

    splits = pd.concat(all_split_times)
    splits.to_csv(output + '_splits.csv')
    fig = plot.visualise_splits(course, splits)
    fig.write_html(output + '_splits.html')

    norm_splits = core.normalise_splits(splits)
    norm_splits.to_csv(output + '_normalised_splits.csv')
    fig = plot.visualise_splits(course, norm_splits, normalised=True)
    fig.write_html(output + '_normalised_splits.html')