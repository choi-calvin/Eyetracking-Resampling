import pandas as pd
import configparser as cp
import os
import argparse
from datetime import datetime

PERCENT_PREC = 3
TIME_PREC = 5
FILE_TYPES = ('.txt', '.text')


def read_config():
    global PERCENT_PREC
    global TIME_PREC
    global FILE_TYPES

    config = cp.ConfigParser()
    config.read('options.ini')

    if 'DEFAULT' in config:
        if 'FILE_TYPES' in config['DEFAULT']:
            FILE_TYPES = tuple(config['DEFAULT']['FILE_TYPES'].split(', '))

    if 'CONSOLE OUTPUT' in config:
        if 'PERCENT_PREC' in config['CONSOLE OUTPUT']:
            PERCENT_PREC = config['CONSOLE OUTPUT']['PERCENT_PREC']
        if 'TIME_PREC' in config['CONSOLE OUTPUT']:
            TIME_PREC = config['CONSOLE OUTPUT']['TIME_PREC']

    return config


def parse_args():
    parser = argparse.ArgumentParser(description="Resample eyetracking data according to parameters.")
    parser.add_argument('dir', help="the directory to scan and apply resampling (default: current directory)",
                        nargs='?', default=os.getcwd())
    return parser.parse_args()


def bin_df(df_old):
    # df_new = df_old.groupby('TRIAL_INDEX')
    df_new = df_old.groupby(df_old.index // 3).mean()

    return df_new


def remove_blinks(df_old):
    blink_count = len(df_old[df_old['RIGHT_IN_BLINK'] == 1])
    df_new = df_old[df_old['RIGHT_IN_BLINK'] == 0]
    print("\tRemoved {} blink(s) ({:.{prec}f}% of total)".format(blink_count, blink_count / len(df_old) * 100,
                                                                 prec=PERCENT_PREC))
    return df_new


def main():
    args = parse_args()
    config = read_config()

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
            df = pd.read_csv(os.path.join(args.dir, filename), sep='\t')
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
