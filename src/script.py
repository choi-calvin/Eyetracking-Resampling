"""
Dataset Resampling Script.

Created By: Christopher Chow and Calvin Choi
Designed For: use in Duncan Lab, University of Toronto
Built On: Python v3.6.4, pandas v0.22.0

For help, run script with help arguments as such:
    $ python script.py -h
or with the long-form:
    $ python script.py --help
"""

import pandas as pd
import numpy as np
import configparser as cp
import os
import math
import argparse
from argparse import RawDescriptionHelpFormatter
from datetime import datetime
from glob import glob

# The name of the .ini config file
# May be renamed but must be within the same directory as this script
CONFIG_FILE = 'options.ini'

# Constants to configure script behaviour
# These are default values, many can be overwritten by the config file
FILE_TYPES = ('txt', 'text', 'csv')
RESAMPLING_MODE = 0
RESAMPLING_RATE = 1000  # rows
RESAMPLING_COUNT = 10
SPECIFY_INTERVAL = 0
FILE_TO_PROCESS = "*"
GROUP_BY = 'TRIAL_INDEX'
PERCENT_PREC = 3
TIME_PREC = 5

# Constants that are used in the aggregation calculations
# Changing these variables will lead to drastic unwanted results
COLUMNS = []
LAST_INDEX = -1
# If the config specifies an aggregation function not in the list below, it warns the user of potential problems
COMMON_AGGREGATE_TYPES = ['mean', 'median', 'sum', 'min', 'max', 'str_mode', 'unique_occurrences']
AGGREGATIONS = {}


def str_to_int(str_to_convert, default):
    """Returns str_to_convert converted to int, or default if an error occurs.

    Args:
        str_to_convert: The str to convert to int.
        default: The int to return instead if the conversion results in an error.

    Returns:
        str_to_convert as an int, or default.
    """
    try:
        converted_str = int(str_to_convert)
        return converted_str
    except ValueError:
        print("ERROR: '{}' is not a valid integer in config, using default {}".format(str_to_convert, default))
    return default


def str_to_float(str_to_convert, default):
    """Returns str_to_convert converted to float, or default if an error occurs.

    Args:
        str_to_convert: The str to convert to float.
        default: The float to return instead if the conversion results in an error.

    Returns:
        str_to_convert as an float, or default.
    """
    try:
        converted_str = float(str_to_convert)
        return converted_str
    except ValueError:
        print("ERROR: '{}' is not a valid integer in config, using default {}".format(str_to_convert, default))
    return default


def str_mode(group):
    """Returns the value that occurs the most in group. For use as an aggregation function.

    Args:
        group: The group to aggregate.

    Returns:
        The mode of group.
    """
    return group.value_counts().index[0]


def unique_occurrences(group):
    """Returns the count of unique occurrences in the group. For use as an aggregation function. Recommended for columns
    with indices, such as blink index.
    NOTE: If used as an aggregation type, unique occurrences are not repeated between consequent groups.

    Args:
        group: The group to aggregate.

    Returns:
        The count of unique occurrences in the group.
    """
    global LAST_INDEX
    uniques = group.unique()
    if len(uniques) > 0 and uniques[0] == LAST_INDEX:
        uniques = uniques[1:]
    uniques = uniques[~np.isnan(uniques)]
    if len(uniques) > 0:
        LAST_INDEX = uniques[-1]
    return len(uniques)


def read_config():
    """Reads options from the config file and stores them in global variables.

    Returns:
        None
    """
    global FILE_TYPES
    global RESAMPLING_MODE
    global RESAMPLING_RATE
    global RESAMPLING_COUNT
    global SPECIFY_INTERVAL
    global GROUP_BY
    global PERCENT_PREC
    global TIME_PREC
    global AGGREGATIONS
    global FILE_TO_PROCESS
    global COLUMNS

    config = cp.ConfigParser()
    config.optionxform = str
    # The config file is looked for in the same directory as the script.
    config.read(os.path.join(os.path.dirname(__file__), CONFIG_FILE))
    if 'SETTINGS' in config:
        if 'FILE_TYPES' in config['SETTINGS']:
            FILE_TYPES = tuple(config['SETTINGS']['FILE_TYPES'].split(','))
        if 'RESAMPLING_MODE' in config['SETTINGS']:
            RESAMPLING_MODE = str_to_int(config['SETTINGS']['RESAMPLING_MODE'], RESAMPLING_MODE)

        if not (0 <= RESAMPLING_MODE <= 2):
            print("RESAMPLING_MODE has an incorrect value, defaulting...")
            RESAMPLING_MODE = 0
        if RESAMPLING_MODE == 0:
            if 'RESAMPLING_RATE' in config['SETTINGS']:
                RESAMPLING_RATE = str_to_float(config['SETTINGS']['RESAMPLING_RATE'], RESAMPLING_RATE) * 1000
            else:
                print("RESAMPLING_RATE not specified, defaulting...")
        elif RESAMPLING_MODE == 1:
            if 'RESAMPLING_COUNT' in config['SETTINGS']:
                RESAMPLING_COUNT = str_to_int(config['SETTINGS']['RESAMPLING_COUNT'], RESAMPLING_COUNT)
            else:
                print("RESAMPLING_COUNT not specified, defaulting...")
        elif RESAMPLING_MODE == 2:
            if 'SPECIFY_INTERVAL' in config['SETTINGS']:
                SPECIFY_INTERVAL = config['SETTINGS']['SPECIFY_INTERVAL', SPECIFY_INTERVAL]
            else:
                print("SPECIFY_INTERVAL not specified, defaulting...")

        if 'GROUP_BY' in config['SETTINGS']:
            GROUP_BY = config['SETTINGS']['GROUP_BY']
            COLUMNS.append(GROUP_BY)
        if 'FILE_TO_PROCESS' in config['SETTINGS']:
            FILE_TO_PROCESS = config['SETTINGS']['FILE_TO_PROCESS']

    if 'AGGREGATE TYPE' in config:
        for variable in config['AGGREGATE TYPE']:
            COLUMNS.append(variable)
            agg_types = config['AGGREGATE TYPE'][variable].split(',')
            for agg_type in agg_types:
                if agg_type not in COMMON_AGGREGATE_TYPES:
                    print(
                        "WARNING: '{}' in config is not a common aggregate type, may cause crashes".format(agg_type))
                if agg_type == 'str_mode':
                    agg_type = str_mode
                if agg_type == 'unique_occurrences':
                    agg_type = unique_occurrences
                if variable in AGGREGATIONS:
                    AGGREGATIONS[variable].append(agg_type)
                else:
                    AGGREGATIONS[variable] = [agg_type]

    if 'CONSOLE OUTPUT' in config:
        if 'PERCENT_PREC' in config['CONSOLE OUTPUT']:
            PERCENT_PREC = str_to_int(config['CONSOLE OUTPUT']['PERCENT_PREC'], PERCENT_PREC)
        if 'TIME_PREC' in config['CONSOLE OUTPUT']:
            TIME_PREC = str_to_int(config['CONSOLE OUTPUT']['TIME_PREC'], TIME_PREC)


def parse_args():
    """Creates and returns an argument parser for the script with appropriate description and arguments.

    Returns:
        An argument parser for the script.
    """
    parser = argparse.ArgumentParser(
        description="Dataset resampling script.",
        epilog="""
        ***
        Resamples all specified file types in the specified directory and outputs in new file with suffix _processed.
        Column variables and their aggregate types are specified in options.ini. If column variables do not exist in a
        dataset, they are skipped.

        Designed for use in Duncan Lab with eyetracking experiment data.
        ***
        """,
        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('dir', help="the directory to scan and apply resampling (default: current directory)",
                        nargs='?', default=os.getcwd())
    return parser.parse_args()


def remove_columns(df):
    """Returns df with columns that are not in COLUMNS (i.e. columns being aggregated) removed.

    Args:
        df: The DataFrame to modify.

    Returns:
        df stripped of unnecessary columns.
    """
    c = list(df.columns.values)
    li = COLUMNS.copy()
    for s in li:
        try:
            c.index(s)
        except ValueError:
            COLUMNS.remove(s)
    return df[COLUMNS]


def remove_blinks(df):
    """Sets rows to NaN in df marked as blink rows and returns it.

    Args:
        df: The DataFrame to modify.

    Returns:
        df stripped of blink rows.
    """
    print("\tRemoving blinks...", end='')
    blink_count = len(df[df['RIGHT_IN_BLINK'] == 1])
    # Rows are set to NaN instead of being removed to maintain the row time intervals.
    df[df['RIGHT_IN_BLINK'] == 1] = np.nan
    print("success!\n\t\tRemoved {} blink(s) ({:.{prec}f}% of total)".format(blink_count,
                                                                             blink_count / len(df) * 100,
                                                                             prec=PERCENT_PREC))
    return df


def grouped(group):
    """Further divides group by the RESAMPLING_RATE and aggregates them, not affecting rows between consequent trials
    with the resampling.

    Args:
        group: The group to divide.

    Returns:
        The new group from aggregation on group.
    """
    global RESAMPLING_RATE
    # Adjust RESAMPLING_RATE according to RESAMPLING_MODE.
    if RESAMPLING_MODE == 1:
        # RESAMPLING_MODE of 1 corresponds to grouping by RESAMPLING_COUNT.
        RESAMPLING_RATE = math.ceil(len(group.index) / RESAMPLING_COUNT)
        if(len(group.index) // RESAMPLING_COUNT==0):
            RESAMPLING_RATE = 1
    group['e'] = pd.Series(range(0, len(group.index), 1), index=group.index)
    new_group = group.groupby((group.e // RESAMPLING_RATE), as_index=False)
    new_group = aggregate(new_group, group)
    return new_group


def bin_df(df_old):
    """Bins df_old by RESAMPLING_RATE, aggregates, and returns the resulting DataFrame.

    Args:
        df_old: The DataFrame to bin and aggregate.

    Returns:
        The resulting DataFrame from performing group by and aggregation on df_old.
    """
    global RESAMPLING_RATE

    # Group every RESAMPLING_RATE rows, and by GROUP_BY to ensure no grouping across trials
    df_groupby = df_old.groupby(GROUP_BY, as_index=True)


    print("\tComputing and aggregating data...",end='')
    df_new = df_groupby.apply(grouped)
    print("success!")
    print("\tGrouped by every {} row(s)".format(RESAMPLING_RATE))

    # Remove the numbered column created in the aggregation
    df_new = df_new.reset_index(level=[None], drop=True)
    return df_new


def aggregate(df_groupby, df):
    """Returns the DataFrame from performing aggregations on df_groupby that are applicable to perform on the original
    df.

    Args:
        df_groupby: The DataFrame to aggregate.
        df: The original DataFrame before performing group by on df_groupby.

    Returns:
        The result of aggregations on df_groupby.
    """
    # Aggregate dataset only with column variables that exist in the current worked dataset
    modified_aggregations = {variable: agg_types for variable, agg_types in AGGREGATIONS.items() if
                             variable in df}
    return df_groupby.agg(modified_aggregations)


def main():
    """Performs specified aggregations on the DataFrames in the specified directory, and outputs them as new DataFrame
    files.

    Returns:
        None
    """
    args = parse_args()
    read_config()
    resampled_count = 0
    error_count = 0  # The number of DataFrames that could not be resampled.

    op_start_time = datetime.now()  # For the calculation of total operation length
    for directory, _, _ in os.walk(args.dir):
        regex_with_all_types = [os.path.join(directory, FILE_TO_PROCESS) + "." + file_type for file_type in
                                list(FILE_TYPES)]
        for regex_with_type in regex_with_all_types:
            for filename in glob(regex_with_type):
                file_split = os.path.splitext(filename)
                # Script ignores all files that end with _processed to avoid processing already processed files.
                if not file_split[0].endswith('_processed'):
                    about_to_override = False
                    file_start_time = datetime.now()  # For current operation length

                    print("Working on '{}':".format(filename))
                    print("\tReading...".format(filename), end='')
                    df = pd.read_csv(os.path.join(args.dir, filename), sep='\t', na_values='.')
                    print("success!")

                    if GROUP_BY not in df.columns:
                        print("\tERROR: '{}' not found in dataset, skipping...".format(GROUP_BY))
                        error_count += 1
                        print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(),
                                                           prec=TIME_PREC))
                        continue

                    df = remove_columns(remove_blinks(df))
                    try:
                        df = bin_df(df)
                    except Exception as e:
                        print("\n\tERROR: " + str(e) + ", skipping...")
                        error_count += 1
                        print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(),
                                                           prec=TIME_PREC))
                        continue

                    new_name = os.path.join(args.dir, file_split[0] + '_processed' + file_split[1])
                    if os.path.isfile(new_name):
                        about_to_override = True
                    print("\tExporting...".format(filename), end='')
                    df.to_csv(new_name, sep='\t')
                    print("success!")
                    if about_to_override:
                        print("\t\tWARNING: Overrode '{}'".format(os.path.abspath(new_name)))
                    print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(),
                                                       prec=TIME_PREC))
                    resampled_count += 1

    print("\n{} dataframe(s) could not be resampled".format(error_count))
    print("Operation success: resampled {} dataframe(s) (total {:.{prec}f}s)".format(resampled_count, (
            datetime.now() - op_start_time).total_seconds(), prec=TIME_PREC))


if __name__ == '__main__':
    main()
