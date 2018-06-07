import pandas as pd
import configparser as cp
import os
import argparse
from datetime import datetime

FILE_TYPES = ('.txt', '.text')
RESAMPLING_RATE = 5
GROUP_BY = 'TRIAL_INDEX'

PERCENT_PREC = 3
TIME_PREC = 5

common_aggregate_types = ['mean', 'median', 'mode', 'sum', 'min', 'max']
aggregations = {}


def str_to_int(str_to_convert, default):
    try:
        converted_str = int(str_to_convert)
        return converted_str
    except ValueError as e:
        print("ERROR: {} in config file is not a valid integer, using default".format(e))
    return default


def read_config():
    global FILE_TYPES
    global RESAMPLING_RATE
    global GROUP_BY
    global PERCENT_PREC
    global TIME_PREC
    global aggregations

    config = cp.ConfigParser()
    config.optionxform = str
    config.read('options.ini')

    if 'SETTINGS' in config:
        if 'FILE_TYPES' in config['SETTINGS']:
            FILE_TYPES = tuple(config['SETTINGS']['FILE_TYPES'].split(', '))
        if 'RESAMPLING_RATE' in config['SETTINGS']:
            RESAMPLING_RATE = str_to_int(config['SETTINGS']['RESAMPLING_RATE'], RESAMPLING_RATE)
        if 'GROUP_BY' in config['SETTINGS']:
            GROUP_BY = config['SETTINGS']['GROUP_BY']

    if 'AGGREGATE TYPE' in config:
        for variable in config['AGGREGATE TYPE']:
            agg_types = config['AGGREGATE TYPE'][variable].split(', ')

            for agg_type in agg_types:
                if agg_type not in common_aggregate_types:
                    print(
                        "WARNING: {} in config file is not a common aggregate type, may cause crashes".format(agg_type))
                if variable in aggregations:
                    aggregations[variable].append(agg_type)
                else:
                    aggregations[variable] = [agg_type]

    if 'CONSOLE OUTPUT' in config:
        if 'PERCENT_PREC' in config['CONSOLE OUTPUT']:
            PERCENT_PREC = str_to_int(config['CONSOLE OUTPUT']['PERCENT_PREC'], PERCENT_PREC)
        if 'TIME_PREC' in config['CONSOLE OUTPUT']:
            TIME_PREC = str_to_int(config['CONSOLE OUTPUT']['TIME_PREC'], TIME_PREC)


def parse_args():
    parser = argparse.ArgumentParser(description="Resample eyetracking data according to parameters.")
    parser.add_argument('dir', help="the directory to scan and apply resampling (default: current directory)",
                        nargs='?', default=os.getcwd())
    return parser.parse_args()


def bin_df(df_old):
    if GROUP_BY not in df_old.columns:
        print("ERROR: {} not found in dataset, exiting...".format(GROUP_BY))
    df_new = df_old.groupby([GROUP_BY, (df_old.index // RESAMPLING_RATE) * RESAMPLING_RATE], as_index=False).agg(
        aggregations)
    df_new = df_new.set_index(GROUP_BY)
    return df_new


def remove_blinks(df_old):
    blink_count = len(df_old[df_old['RIGHT_IN_BLINK'] == 1])
    df_new = df_old[df_old['RIGHT_IN_BLINK'] == 0]
    print("\tRemoved {} blink(s) ({:.{prec}f}% of total)".format(blink_count, blink_count / len(df_old) * 100,
                                                                 prec=PERCENT_PREC))
    return df_new


def main():
    args = parse_args()
    read_config()

    resampled_count = 0

    op_start_time = datetime.now()
    directory = os.fsencode(args.dir)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        filesplit = os.path.splitext(filename)
        if filename.endswith(FILE_TYPES) and not filesplit[0].endswith('_processed'):
            file_start_time = datetime.now()

            print("Working on {}:".format(filename))
            print("\tReading...".format(filename))
            df = pd.read_csv(os.path.join(args.dir, filename), sep='\t', na_values='.')
            df = remove_blinks(df)
            df = bin_df(df)

            new_name = os.path.join(args.dir, filesplit[0] + '_processed' + filesplit[1])
            print("\tExporting...".format(filename))
            if os.path.isfile(new_name):
                print("\t\tWARNING: Overriding {}".format(os.path.abspath(new_name)))
            df.to_csv(new_name, sep='\t')
            print("\tExport successful!")
            print("\tTotal {:{prec}f}s".format((datetime.now() - file_start_time).total_seconds(), prec=TIME_PREC))
            resampled_count += 1

    print("Operation success: resampled {} dataframe(s) (total {:.{prec}f}s)".format(resampled_count, (
            datetime.now() - op_start_time).total_seconds(), prec=TIME_PREC))


if __name__ == '__main__':
    main()
