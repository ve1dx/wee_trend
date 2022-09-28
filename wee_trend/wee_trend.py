# -*- coding: utf-8 -*-
#
# Paul Dunphy, Dr Michael Dunphy- 2022
#

import wee_trend.wee_trenddata as wtdata

import argparse
import calendar
import datetime
import glob
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.stats
import sys
import tqdm

matplotlib.use("Agg")


def get_choice(prompt, lo, hi):
    while True:
        choice = input(prompt + ': ')
        try:
            choice = int(choice)
        except ValueError:
            print("Character not valid - try again")
            continue
        if not lo <= choice <= hi:
            print("Choice must be between {} and {} - try again".format(lo, hi))
            continue
        return choice


def menu(int_month):
    text_month = calendar.month_name[int_month]
    lo, hi = 1, 12
    print()
    print()
    while True:
        print_menu(int_month, wtdata.menudata)
        option = get_choice("Enter your choice", lo, hi)
        if option == 11:
            int_month, text_month = get_month()
            print()
            print()
            print("Switched month to", text_month)
        else:
            break
    if option == 12:
        print()
        print("Exiting program.")
        sys.exit(0)
    print(wtdata.menudata[option]["title"], "being processed")
    return int_month, option, text_month


def print_menu(i_month, men_data):
    text_month = calendar.month_name[i_month]
    print(text_month, "selected")
    for key in men_data:
        print(key, "--", men_data[key]["title"])


def make_heading_title(number, text_month, station_location):
    if station_location == "NONE":
        return (
            wtdata.menudata[number]["heading"],
            wtdata.menudata[number]["title"] + " - " + text_month,
        )
    else:
        return (
            wtdata.menudata[number]["heading"],
            wtdata.menudata[number]["title"] + " -" + station_location + " - " + text_month,
        )


def get_month():
    lo, hi = 1, 12
    input_month = get_choice("Enter month (1-12)", lo, hi)
    month_name = calendar.month_name[input_month]
    return input_month, month_name


def get_month_list(the_path):
    glob_string = os.path.join(the_path, 'NOAA-????-??.txt')
    master_list = glob.glob(glob_string)
    if len(master_list) == 0:
        print("No NOAA files found in", the_path, "Exiting program.")
        sys.exit(0)
    master_list.sort()
    with open(master_list[0], "r") as in_file:
        data = in_file.readlines()
        station_location_line = data[3]
        station_location = station_location_line.split(":")[1]
        station_location = station_location.rstrip()
        unit_line = data[7]
        precipitation_unit = unit_line[42:44]
        if precipitation_unit == 'in':
            return master_list, station_location, wtdata.unitdata['US']
        elif precipitation_unit == 'mm':
            return master_list, station_location, wtdata.unitdata['METRICWX']
        elif precipitation_unit == 'cm':
            return master_list, station_location, wtdata.unitdata['METRIC']
        else:
            print("Unable to determine units. Please check NOAA files for correct format")
            sys.exit(0)


def load_months(month_list):
    dflist = []
    for fully_qualified in month_list:
        pathname, current_file = os.path.split(fully_qualified)
        yy = int(current_file[5:9])
        mm = int(current_file[10:12])
        _, month_days = calendar.monthrange(yy, mm)
        df = pd.read_fwf(
            fully_qualified,
            names=wtdata.headings,
            header=0,
            colspecs=wtdata.colspecs,
            skiprows=12,
            nrows=month_days,
        )
        df['date'] = list(map(lambda d: datetime.datetime(yy, mm, d), df['DAY'].to_list()))
        dflist += [df]
    dfout = pd.concat(dflist, ignore_index=True).set_index('date')
    return dfout


def check_for_complete_month(year, month, current_month_df, missing_days):
    _, month_days = calendar.monthrange(year, month)
    valid_days = month_days - missing_days
    number_of_valid_days = np.sum(~current_month_df.isna().any(axis=1))
    return number_of_valid_days >= valid_days


def process_months(all_data_df, requested_column, requested_month, tolerance,
                   verbose_level, incomplete_months):
    incomplete = incomplete_months
    years = sorted(set(all_data_df.index.year.to_list()))
    dropped = 0
    years_out, values_out = [], []
    years_month_df = all_data_df[all_data_df.index.month == requested_month]  # Subset first for performance gain
    for year in years:
        month_df = years_month_df.loc[years_month_df.index.year == year]  # subset down inside this loop
        should_keep = check_for_complete_month(year, requested_month, month_df, tolerance)
        test_month = '{}-{:02d}'.format(year, requested_month)
        if not should_keep:
            if test_month not in incomplete:
                incomplete.append(test_month)
                dropped += 1
                if verbose_level == 1:
                    print("Working on month", test_month, flush=True)
                    print("Tolerance for missing days is", tolerance, flush=True)
                    print("Data for {}-{:02d} incomplete, dropping it".format(year, requested_month), flush=True)
                    print("Number of", calendar.month_name[requested_month], "months dropped =", dropped, flush=True)
            continue
        # Only the temperature range is a calculated value. The rest are
        # extracted from the specified month's dataframe.
        if requested_column == "TEMP_RANGE":
            value = month_df["HIGH_TEMP"].max() - month_df["LOW_TEMP"].min()
        elif requested_column in ["MEAN_TEMP", "AVG_WIND_SPEED", "DOMINANT_WIND_DIRECTION"]:
            value = month_df[requested_column].mean()
        elif requested_column in ["HIGH_TEMP", "HIGH_WIND_GUST"]:
            value = month_df[requested_column].max()
        elif requested_column in ["LOW_TEMP"]:
            value = month_df[requested_column].min()
        elif requested_column in ["HEAT_DEG_DAYS", "COOL_DEG_DAYS", "PRECIPITATION"]:
            value = month_df[requested_column].sum()
        else:
            print("Can only process items specified in the menu.")
            print("Exiting program with no processing")
            sys.exit()
        years_out += [year]
        values_out += [value]

    # Put data into a dataframe ready to plot
    plot_prep_df = pd.DataFrame({"int": years_out, "float": values_out})
    plot_prep_df.columns = ["Year", "Mth"]
    plot_prep_df['Mth'] = plot_prep_df['Mth'].replace(np.nan, 0.0)
    return plot_prep_df, dropped, incomplete


def plot_graph(xvals, yvals, title, plot_path, units):
    #
    # Green as color for points
    #
    plt.plot(xvals, yvals, "o", color="green")
    #
    # Obtain m (slope) and b (intercept) of linear regression line
    #
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(xvals, yvals)
    r_sq = r_value ** 2
    #
    # Add a red coloured linear regression line
    #
    plt.annotate(
        "R\u00b2 = {:.2f}".format(r_sq), xy=(np.median(xvals), np.median(yvals))
    )
    plt.plot(xvals, slope * xvals + intercept, color="red")
    #
    # Title & labels
    #
    plt.title(title)
    plt.xlabel("Year")
    t_units = units['temp']
    p_units = units['precip']
    s_units = units['speed']
    if "Direction" in title:
        plt.ylabel("Direction")
    elif "Precipitation" in title:
        plt.ylabel(p_units)
    elif "Wind" in title:
        plt.ylabel(s_units)
    elif "Range" in title:
        plt.ylabel("Temp Swing " + t_units)
    else:
        plt.ylabel("Temp " + t_units)
    #
    # Save the figure
    #
    underscored_name = title.replace(",", "").replace("- ", "").replace(" ", "_")
    plot_save = os.path.join(plot_path, underscored_name)
    plt.savefig(plot_save)
    plt.close()


def python_check():
    version_major = sys.version_info[0]
    version_minor = sys.version_info[1]
    version_micro = sys.version_info[2]
    if not (version_major == 3 and version_minor >= 5):
        print("Python verson 3.5 or higher required to run wee_trend. This system is running Python version ",
              version_major, ".", version_minor, ".", version_micro, sep="")
        print()
        print("Exiting program.")
        sys.exit(0)


def common_processing(option, text_month, station_location, all_data_df, month, tolerance,
                      verbose_level, incomplete, plot_path, units):
    heading_variable, plot_title = make_heading_title(option, text_month, station_location)
    plot_ready_df, dumped_months, incomplete_months = process_months(all_data_df,
                                                                     heading_variable,
                                                                     month, tolerance, verbose_level, incomplete)
    x = plot_ready_df["Year"]
    y = plot_ready_df["Mth"]
    plot_graph(x, y, plot_title, plot_path, units)
    return dumped_months, incomplete_months


def run_interactive(month_list, station_location, plot_path, tolerance, verbose_level, units):
    incomplete_months = []
    int_month, text_month = get_month()
    all_data_df = load_months(month_list)
    while True:
        month, option, text_month = menu(int_month)
        common_processing(option, text_month, station_location, all_data_df, month,
                          tolerance, verbose_level, incomplete_months, plot_path, units)


def run_batch(month_list, station_location, plot_path, tolerance, verbose_level, units):
    incomplete_months = []
    print()
    print("Processing all combinations within NOAA files in batch mode. This may take a moment.")
    print()
    total_dumped_months = 0
    all_data_df = load_months(month_list)
    if verbose_level != 1:
        progressbar = tqdm.tqdm(total=len(wtdata.batchmonth) * len(wtdata.batchoptions))
    for month in wtdata.batchmonth:
        text_month = calendar.month_name[month]
        for option in wtdata.batchoptions:
            if verbose_level == 1:
                print("Processing month", text_month, flush=True)
            dumped_months, incomplete = common_processing(option, text_month, station_location,
                                                          all_data_df, month,
                                                          tolerance, verbose_level, incomplete_months,
                                                          plot_path, units)
            total_dumped_months = total_dumped_months + dumped_months
            if verbose_level != 1:
                progressbar.update()
    if verbose_level != 1:
        progressbar.close()
    print()
    print()
    print("All combinations plotted")
    print("Total months dropped =", total_dumped_months)
    print("Re-run with the -V 1 option to see which ones were dropped.")
    print("Exiting Program")


def main():
    try:
        python_check()
        home = os.path.expanduser("~")
        plot_path = os.path.join(home, "wee_trend_plots/")
        my_parser = argparse.ArgumentParser(
            prog="wee_trend",
            formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40, ), )
        my_parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
        group = my_parser.add_mutually_exclusive_group()
        group.add_argument('-i', '--interactive',
                           help='user interactively selects month and data to be plotted',
                           action='store_true',
                           )
        group.add_argument('-b', '--batch',
                           help='all combinations of months and data are plotted',
                           action='store_true',
                           )
        my_parser.add_argument('-n', '--noaa',
                               help='input path to NOAA files (default is /var/www/html/weewx/NOAA/)',
                               action='store',
                               default='/var/www/html/weewx/NOAA/',
                               )
        my_parser.add_argument('-p', '--plot',
                               help="output path for plots (default is " + plot_path + ")",
                               action='store',
                               default=plot_path,
                               )
        my_parser.add_argument('-l', '--location',
                               help='Station location for plot headings (default is from NOAA files, or ''NONE)',
                               choices=("NF", "NONE"),
                               action="store",
                               default="NF",
                               )
        my_parser.add_argument('-t', '--tolerance',
                               default=0,
                               type=int,
                               choices=range(0, 26),
                               action='store',
                               metavar='0-25',
                               help='Number of days in a month with missing data allowed. (default is 0, '
                                    'max is 25)',
                               )
        my_parser.add_argument('-V', '--VERBOSE',
                               default=0,
                               type=int,
                               choices=range(0, 2),
                               action='store',
                               metavar='0-1',
                               help="Change verbosity level (default is 0)")
        my_parser.epilog = (
            '-i and -b options are mutually exclusive. The default is batch.'
        )
        args = my_parser.parse_args()
        if args.interactive:
            mode = 'interactive'
        else:
            mode = 'batch'
        data_path = args.noaa
        plot_path = args.plot
        station_location_source = args.location
        missing_allowed = args.tolerance
        verbose_level = args.VERBOSE
        if not os.path.exists(data_path):
            print("NOAA directory", data_path, "does not exist. Exiting program.")
            sys.exit(0)
        if not os.path.exists(plot_path):
            print("PLOT directory", plot_path, "does not exist. Creating it.")
            os.makedirs(plot_path, exist_ok=True)
        month_list, station_location_from_files, units = get_month_list(data_path)
        if station_location_source == "NF":
            station_location = station_location_from_files
        else:
            station_location = "NONE"
        if mode == 'interactive':
            run_interactive(month_list, station_location, plot_path, missing_allowed, verbose_level, units)
        else:
            run_batch(month_list, station_location, plot_path, missing_allowed, verbose_level, units)
    except KeyboardInterrupt:
        print()
        print("Keyboard interrupt by user")
        print()
        print()
