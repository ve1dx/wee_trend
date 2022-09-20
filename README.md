# wee_trend

A program to look for trends in weewx generated NOAA files. The results may not be statistically significant. The rule of thumb is 20 years of data to look for climate signals. Otherwise, we have just sampled some inter-annual variability. Climatology experts say we need 30 or 50 years to be sure, with 20 years considered a bare minimum. weewx users may still wish to look for trends within their data.

Requires Python version 3.5 or higher and has been tested on Debian 11 (64-bit), Ubuntu 22.04 and MAC OS X (macOS Monterey 12.5.1). This program should run on Windows equipped with Python 3.5 or later. It is designed to analyze the output of weewx. The user must transfer the weewx NOAA files from a weewx install if run on a different system.


To install, download weather_trend-main.zip, and extract and install it:

unzip weather_trend-main.zip

cd weather_trend-main

pip install -e .

The wee_trend command should then work from anywhere.

To remove:

pip uninstall wee_trend

Use wee_trend --help for more info

On non-weew implementations, create a directory for the NOAA files. This directory  needs to have monthly weewx generated NOAA files. On weewx installs this already exists, usually in /var/www/html/weewx/NOAA


Python libraries required:

pandas
numpy
scipy
matplotlib



Run the analysis program as follows:

Interactively if you want to select a few plots:

wee_trend -i


In batch mode if you want all plots possible:
    
wee_trend
    
Note that all plots will be generated in batch mode or may be requested in interactive mode, but some may not make meteorological sense for all geographical locations. Most QC issues, such as missing or defective sensors, are QC items that need to be considered by the user.


The plots are created as .png files in $HOME/wee_trend_plots/

Demo NOAA files in US and METRIC format are included to test your install.
