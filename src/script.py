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
import argparse
from argparse import RawDescriptionHelpFormatter
from datetime import datetime
from glob import glob

# Constants, can be overwritten by config file
CONFIG_FILE = 'options.ini'

FILE_TYPES = ('txt', 'text', 'csv')
RESAMPLING_RATE = 1000  # rows
FILE_TO_PROCESS = "*"
GROUP_BY = 'TRIAL_INDEX'

PERCENT_PREC = 3
TIME_PREC = 5

LAST_INDEX = -1

COMMON_AGGREGATE_TYPES = ['mean', 'median', 'sum', 'min', 'max', 'str_mode', 'unique_occurrences']
AGGREGATIONS = {}


def str_to_int(str_to_convert, default):
    try:
        converted_str = int(str_to_convert)
        return converted_str
    except ValueError:
        print("ERROR: '{}' is not a valid integer in config, using default {}".format(str_to_convert, default))
    return default


def str_to_float(str_to_convert, default):
    try:
        converted_str = float(str_to_convert)
        return converted_str
    except ValueError:
        print("ERROR: '{}' is not a valid integer in config, using default {}".format(str_to_convert, default))
    return default


def str_mode(group):
    return group.value_counts().index[0]


def unique_occurrences(group):
    global LAST_INDEX
    uniques = group.unique()
    if len(uniques) > 0 and uniques[0] == LAST_INDEX:
        uniques = uniques[1:]
    uniques = uniques[~np.isnan(uniques)]
    if len(uniques) > 0:
        LAST_INDEX = uniques[-1]
    return len(uniques)


# Overwrite constants from config file, if they exist
def read_config():
    global FILE_TYPES
    global RESAMPLING_RATE
    global GROUP_BY
    global PERCENT_PREC
    global TIME_PREC
    global AGGREGATIONS
    global FILE_TO_PROCESS

    config = cp.ConfigParser()
    config.optionxform = str
    config.read(CONFIG_FILE)  # By default, config file is named 'options.ini' in the same folder as script

    if 'SETTINGS' in config:
        if 'FILE_TYPES' in config['SETTINGS']:
            FILE_TYPES = tuple(config['SETTINGS']['FILE_TYPES'].split(','))
        if 'RESAMPLING_RATE' in config['SETTINGS']:
            RESAMPLING_RATE = str_to_float(config['SETTINGS']['RESAMPLING_RATE'], RESAMPLING_RATE) * 1000
        if 'GROUP_BY' in config['SETTINGS']:
            GROUP_BY = config['SETTINGS']['GROUP_BY']
        if 'FILE_TO_PROCESS' in config['SETTINGS']:
            FILE_TO_PROCESS = config['SETTINGS']['FILE_TO_PROCESS']

    if 'AGGREGATE TYPE' in config:
        for variable in config['AGGREGATE TYPE']:
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


def remove_blinks(df):
    print("\tRemoving blinks...", end='')
    blink_count = len(df[df['RIGHT_IN_BLINK'] == 1])
    df[df['RIGHT_IN_BLINK'] == 1] = np.nan
    print("success!\n\t\tRemoved {} blink(s) ({:.{prec}f}% of total)".format(blink_count,
                                                                             blink_count / len(df) * 100,
                                                                             prec=PERCENT_PREC))


def grouped(group):
    group['e'] = pd.Series(range(0, len(group.index), 1), index=group.index)
    new_group = group.groupby((group.e//RESAMPLING_RATE), as_index=False)
    new_group = aggregate(new_group, group)
    return new_group


def bin_df(df_old):
    # Group every RESAMPLING_RATE rows, and by GROUP_BY to ensure no grouping across trials
    print("\tGrouping every {} row(s)...".format(RESAMPLING_RATE), end='')
    df_groupby = df_old.groupby(GROUP_BY, as_index=True)
    print("success!")
    print("\tComputing and aggregating data...", end='')
    df_new = df_groupby.apply(grouped)  # Drop rows at the end of each group to match sampling rate
    print("success!")
    return df_new


def aggregate(df_groupby, df):
    # Aggregate dataset only with column variables that exist in the current worked dataset
    modified_aggregations = {variable: agg_types for variable, agg_types in AGGREGATIONS.items() if
                             variable in df}
    return df_groupby.agg(modified_aggregations)


def main():
    args = parse_args()
    read_config()

    resampled_count = 0
    error_count = 0

    op_start_time = datetime.now()  # For the calculation of total operation length
    for dir, _, _ in os.walk(args.dir):
        regex_with_all_types = [os.path.join(dir, FILE_TO_PROCESS) + "." + file_type for file_type in list(FILE_TYPES)]
        for regex_with_type in regex_with_all_types:
            for filename in glob(regex_with_type):
                file_split = os.path.splitext(filename)
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

                    remove_blinks(df)
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
