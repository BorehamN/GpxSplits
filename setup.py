from setuptools import setup, find_packages

setup(
    name='gpxsplits',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'plotly',
        'numpy',
        'pandas',
        'shapely',
    ],
    entry_points={
        'console_scripts': [
            'gpxsplits = gpxsplits.main:gpxsplits',
            'gpxtocsv = gpxsplits.main:gpxtocsv',
        ],
    },
)