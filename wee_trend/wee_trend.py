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


def menu(int_month, men_data, loc):
    text_month = calendar.month_name[int_month]
    lo, hi = 1, 12
    print()
    print()
    while True:
        print_menu(int_month, men_data)
        option = get_choice("Enter your choice", lo, hi)
        if option == 11:
            int_month, text_month = get_month()
            option11(int_month)
        else:
            break
    if option == 12:
        print()
        print("Exiting program.")
        sys.exit(0)
    heading, title = option_1_10(option, text_month, men_data, loc)
    return heading, title, int_month


def print_menu(i_mnth, men_data):
    text_mnth = calendar.month_name[i_mnth]
    print(text_mnth, "selected")
    for key in men_data:
        print(key, "--", men_data[key]["description"])


def option11(i_mnth):
    text_month = calendar.month_name[i_mnth]
    print()
    print()
    print("Switched month to", text_month, flush=True)


def option_1_10(number, txt_month, men_data, loc):
    print(men_data[number]["description"], "being processed")
    head, title = make_heading_title(number, txt_month, loc)
    return head, title


def make_heading_title(number, txt_month, locn):
    if locn == "NONE":
        return (
            wtdata.menudata[number]["heading"],
            wtdata.menudata[number]["title"] + " - " + txt_month,
        )
    else:
        return (
            wtdata.menudata[number]["heading"],
            wtdata.menudata[number]["title"] + " -" + locn + " - " + txt_month,
        )


def get_month():
    lo, hi = 1, 12
    input_mnth = get_choice("Enter month (1-12)", lo, hi)
    m_name = calendar.month_name[input_mnth]
    return input_mnth, m_name


def get_month_list(the_path):
    glob_string = os.path.join(the_path, 'NOAA-????-??.txt')
    master_list = glob.glob(glob_string)
    if len(master_list) == 0:
        print("No NOAA files found in", the_path, "Exiting program.")
        sys.exit(0)
    master_list.sort()
    with open(master_list[0], "r") as in_file:
        data = in_file.readlines()
        loc_line = data[3]
        qth = loc_line.split(":")[1]
        the_qth = qth.rstrip()
    return master_list, the_qth


def get_units(first_file):
    with open(first_file, "r") as temp_file:
        temp_data = temp_file.readlines()
    unit_line = temp_data[7]
    precip_unit = unit_line[42:44]
    if precip_unit == 'in':
        return wtdata.unitdata['US']
    elif precip_unit == 'mm':
        return wtdata.unitdata['METRICWX']
    elif precip_unit == 'cm':
        return wtdata.unitdata['METRIC']
    else:
        print("Unable to determine units. Please check NOAA files for correct format")
        sys.exit(0)


def load_months(month_list):
    dflist = []
    for fully_qualified in month_list:
        pathname, current_file = os.path.split(fully_qualified)
        yy = int(current_file[5:9])
        mm = int(current_file[10:12])
        _, mnth_days = calendar.monthrange(yy, mm)
        df = pd.read_fwf(
            fully_qualified,
            names=wtdata.headings,
            header=0,
            colspecs=wtdata.colspecs,
            skiprows=12,
            nrows=mnth_days,
        )
        df['date'] = list(map(lambda d: datetime.datetime(yy, mm, d), df['DAY'].to_list()))
        dflist += [df]
    dfout = pd.concat(dflist, ignore_index=True).set_index('date')
    return dfout


def check_for_complete_month(year, month, current_month_df, miss_days):
    _, mnth_days = calendar.monthrange(year, month)
    valid_days = mnth_days - miss_days
    n_valid_days = np.sum(~current_month_df.isna().any(axis=1))
    return n_valid_days >= valid_days


def process_months(all_data_df, month_list, requested_column, requested_month, tolerance,
                   verbosity, incomplete_months):
    years = sorted(set(all_data_df.index.year.to_list()))
    units = get_units(month_list[0])
    dropped = 0
    years_out, values_out = [], []
    for year in years:
        month_df = all_data_df.loc[(all_data_df.index.month == requested_month) & (all_data_df.index.year == year)]
        should_keep = check_for_complete_month(year, requested_month, month_df, tolerance)
        test_month = '{}-{:02d}'.format(year, requested_month)
        if not should_keep:
            if test_month not in incomplete_months:
                incomplete_months.append(test_month)
                dropped += 1
                if verbosity == 1:
                    print("Working on month", test_month, flush=True)
                    print("Tolerance for missing days is", tolerance, flush=True)
                    print("Data for {}-{:02d} incomplete, dropping it".format(year, requested_month), flush=True)
                    print("Number of", calendar.month_name[requested_month], "months dropped =", dropped)
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
    return plot_prep_df, dropped, units


def plot_graph(xvals, yvals, title, p_path, units):
    t_uts = units['temp']
    p_uts = units['precip']
    s_uts = units['speed']
    plt.cla()
    plt.xlabel("Year")
    if "Direction" in title:
        plt.ylabel("Direction")
    elif "Precipitation" in title:
        plt.ylabel(p_uts)
    elif "Wind" in title:
        plt.ylabel(s_uts)
    elif "Range" in title:
        plt.ylabel("Temp Swing " + t_uts)
    else:
        plt.ylabel("Temp " + t_uts)
    #
    # Green as color for points
    #
    plt.plot(xvals, yvals, "o", color="green")
    #
    # Add a title
    #
    plt.title(title)
    plt.scatter(xvals, yvals)
    #
    # Obtain m (slope) and b(intercept) of linear regression line
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
    underscored_name = title.replace(",", "").replace("- ", "").replace(" ", "_")
    plot_save = os.path.join(p_path, underscored_name)
    plt.savefig(plot_save)
    plt.clf()
    plt.close()


def python_check():
    ver_maj = sys.version_info[0]
    ver_min = sys.version_info[1]
    ver_mic = sys.version_info[2]
    if not (ver_maj == 3 and ver_min >= 5):
        print("Python verson 3.5 or higher required to run wee_trend. This system is running Python version ",
              ver_maj, ".", ver_min, ".", ver_mic, sep="")
        print()
        print("Exiting program.")
        sys.exit(0)


def run_interactive(mnth_list, locn, p_path, tolerate, verbosity):
    incomplete_months = []
    int_month, text_mnth = get_month()
    all_available_data_df = load_months(mnth_list)
    while True:
        heading_variable, plot_title, int_month = menu(int_month, wtdata.menudata, locn)
        plot_ready_df, dumped, units = process_months(all_available_data_df, mnth_list,
                                                      heading_variable, int_month, tolerate, verbosity,
                                                      incomplete_months)
        x = plot_ready_df["Year"]
        y = plot_ready_df["Mth"]
        plot_graph(x, y, plot_title, p_path, units)


def run_batch(mnth_list, loc, p_path, tolerate, verbose_extent):
    print()
    print("Processing all combinations within NOAA files in batch mode. This may take a moment.")
    print()
    total_dumped = 0
    incomplete_months = []
    all_available_data_df = load_months(mnth_list)
    for month in wtdata.batchmonth:
        txt_month = calendar.month_name[month]
        for option in wtdata.batchoptions:
            if verbose_extent == 1:
                print("Processing month", txt_month, flush=True)
            heading_variable, plot_title = make_heading_title(option, txt_month, loc)
            plot_ready_df, dumped, units = process_months(all_available_data_df, mnth_list, heading_variable,
                                                          month, tolerate, verbose_extent, incomplete_months)
            x = plot_ready_df["Year"]
            y = plot_ready_df["Mth"]
            if verbose_extent == 0:
                print(". ", end="", flush=True)
            plot_graph(x, y, plot_title, p_path, units)
            total_dumped = total_dumped + dumped
    print()
    print()
    print("All combinations plotted")
    print("Total months dropped =", total_dumped)
    print("Re-run with the -V 1 option to see which ones were dropped.")
    print("Exiting Program")


#   sys.exit(0)


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
                               help='Location for plot headings (default is NOAA files, suppress with NONE)',
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
        location_source = args.location
        missing_allowed = args.tolerance
        verbose_level = args.VERBOSE
        if not os.path.exists(data_path):
            print("NOAA directory", data_path, "does not exist. Exiting program.")
            sys.exit(0)
        if not os.path.exists(plot_path):
            print("PLOT directory", plot_path, "does not exist. Creating it.")
            os.makedirs(plot_path, exist_ok=True)
        month_list, location_found_in_files = get_month_list(data_path)
        if location_source == "NF":
            location = location_found_in_files
        else:
            location = "NONE"
        if mode == 'interactive':
            run_interactive(month_list, location, plot_path, missing_allowed, verbose_level)
        else:
            run_batch(month_list, location, plot_path, missing_allowed, verbose_level)
    except KeyboardInterrupt:
        print()
        print("Keyboard interrupt by user")
        print()
        print()
