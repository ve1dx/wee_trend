
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='wee_trend',
    version='0.1.0',
    description='A program to look for trends in weewx generated NOAA files.',
    long_description=readme,
    author='Paul Dunphy',
    include_package_data=True,
    packages=find_packages(),
    url='https://github.com/ve1dx/weather_trend',
    entry_points={
        'console_scripts': ['wee_trend=wee_trend.wee_trend:main'],
    },
)
