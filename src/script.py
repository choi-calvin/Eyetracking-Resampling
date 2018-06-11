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
import configparser as cp
import os
import argparse
from argparse import RawDescriptionHelpFormatter
from datetime import datetime

# Constants, can be overwritten by config file or script arguments
CONFIG_FILE = 'options.ini'

FILE_TYPES = ('txt', 'text')
RESAMPLING_RATE = 5
GROUP_BY = 'TRIAL_INDEX'

PERCENT_PREC = 3
TIME_PREC = 5

COMMON_AGGREGATE_TYPES = ['mean', 'median', 'mode', 'sum', 'min', 'max']
AGGREGATIONS = {}


def str_to_int(str_to_convert, default):
    try:
        converted_str = int(str_to_convert)
        return converted_str
    except ValueError:
        print("ERROR: '{}' is not a valid integer in config, using default {}".format(str_to_convert, default))
    return default


# Overwrite constants from config file, if they exist
def read_config():
    global FILE_TYPES
    global RESAMPLING_RATE
    global GROUP_BY
    global PERCENT_PREC
    global TIME_PREC
    global AGGREGATIONS

    config = cp.ConfigParser()
    config.optionxform = str
    config.read(CONFIG_FILE)  # By default, config file is named 'options.ini' in the same folder as script

    if 'SETTINGS' in config:
        if 'FILE_TYPES' in config['SETTINGS']:
            FILE_TYPES = tuple(config['SETTINGS']['FILE_TYPES'].split(','))
        if 'RESAMPLING_RATE' in config['SETTINGS']:
            RESAMPLING_RATE = str_to_int(config['SETTINGS']['RESAMPLING_RATE'], RESAMPLING_RATE)
        if 'GROUP_BY' in config['SETTINGS']:
            GROUP_BY = config['SETTINGS']['GROUP_BY']

    if 'AGGREGATE TYPE' in config:
        for variable in config['AGGREGATE TYPE']:
            agg_types = config['AGGREGATE TYPE'][variable].split(',')

            for agg_type in agg_types:
                if agg_type not in COMMON_AGGREGATE_TYPES:
                    print(
                        "WARNING: '{}' in config is not a common aggregate type, may cause crashes".format(agg_type))
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
    parser.add_argument('-n', help="the resampling rate", nargs='?', default=RESAMPLING_RATE, type=int,
                        dest='resampling_rate')
    parser.add_argument('--trial', help="the name of the column specifying trial indices",
                        nargs='?', default=GROUP_BY, dest='trial_variable')
    return parser.parse_args()


# Overwrite constants from arguments, if set
def update_args(args):
    global GROUP_BY
    global RESAMPLING_RATE

    if args.trial_variable is not None:
        GROUP_BY = args.trial_variable
    if args.resampling_rate is not None:
        RESAMPLING_RATE = args.resampling_rate


def remove_blinks(df_old):
    print("\tRemoving blinks...", end='')
    blink_count = len(df_old[df_old['RIGHT_IN_BLINK'] == 1])
    df_new = df_old[df_old['RIGHT_IN_BLINK'] == 0]
    print("success!\n\t\tRemoved {} blink(s) ({:.{prec}f}% of total)".format(blink_count,
                                                                             blink_count / len(df_old) * 100,
                                                                             prec=PERCENT_PREC))
    return df_new


def bin_df(df_old):
    # Group every RESAMPLING_RATE rows, and by GROUP_BY to ensure no grouping across trials
    print("\tGrouping every {} row(s)...".format(RESAMPLING_RATE), end='')
    df_groupby = df_old.groupby([GROUP_BY, (df_old.index // RESAMPLING_RATE) * RESAMPLING_RATE], as_index=False)
    # Drop rows at the end of each group to match sampling rate
    # df_groupby = df_groupby.filter(lambda x: len(x.index) == RESAMPLING_RATE)
    # df_groupby = df_groupby.groupby([GROUP_BY, (df_groupby.index // RESAMPLING_RATE) * RESAMPLING_RATE], as_index=False)
    print("success!")
    print("\tComputing and aggregating data...", end='')
    df_new = aggregate(df_groupby, df_old)
    print("success!")
    df_new = df_new.set_index(GROUP_BY)
    return df_new


def aggregate(df_groupby, df):
    # Aggregate dataset only with column variables that exist in the current worked dataset
    modified_aggregations = {variable: agg_types for variable, agg_types in AGGREGATIONS.items() if
                             variable in df}
    return df_groupby.agg(modified_aggregations)


def main():
    args = parse_args()
    read_config()
    update_args(args)

    resampled_count = 0
    error_count = 0

    op_start_time = datetime.now()  # For the calculation of total operation length
    directory = os.fsencode(args.dir)
    for file in os.listdir(directory):
        about_to_override = False

        filename = os.fsdecode(file)
        file_split = os.path.splitext(filename)
        if filename.endswith(FILE_TYPES) and not file_split[0].endswith('_processed'):
            file_start_time = datetime.now()  # For current operation length

            print("Working on '{}':".format(filename))
            print("\tReading...".format(filename), end='')
            df = pd.read_csv(os.path.join(args.dir, filename), sep='\t', na_values='.')
            print("success!")

            if GROUP_BY not in df.columns:
                print("\tERROR: '{}' not found in dataset, skipping...".format(GROUP_BY))
                error_count += 1
                print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(), prec=TIME_PREC))
                continue

            df = remove_blinks(df)
            try:
                df = bin_df(df)
            except AttributeError as e:
                print("\n\tERROR: " + str(e) + ", skipping...")
                error_count += 1
                print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(), prec=TIME_PREC))
                continue

            new_name = os.path.join(args.dir, file_split[0] + '_processed' + file_split[1])
            if os.path.isfile(new_name):
                about_to_override = True
            print("\tExporting...".format(filename), end='')
            df.to_csv(new_name, sep='\t')
            print("success!")
            if about_to_override:
                print("\t\tWARNING: Overrode '{}'".format(os.path.abspath(new_name)))
            print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(), prec=TIME_PREC))
            resampled_count += 1

    print("\n{} dataframe(s) could not be resampled".format(error_count))
    print("Operation success: resampled {} dataframe(s) (total {:.{prec}f}s)".format(resampled_count, (
            datetime.now() - op_start_time).total_seconds(), prec=TIME_PREC))


if __name__ == '__main__':
    main()
