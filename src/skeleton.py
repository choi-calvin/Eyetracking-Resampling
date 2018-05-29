import pandas as pd
import configparser as cp
import os
import argparse
from datetime import datetime


def read_config():
    config = cp.ConfigParser()
    config.read("options.ini")
    option = config['DEFAULT']
    return option


def parse_args():
    parser = argparse.ArgumentParser(description='Resample eyetracking data according to parameters.')
    parser.add_argument('dir', help='the directory to scan and apply resampling (default: current directory)',
                        nargs='?', default=os.getcwd())
    return parser.parse_args()


def manipulate_df(df_old):
    blink_count = len(df_old['RIGHT_IN_BLINK'] == 1)
    df_new = df_old[df_old['RIGHT_IN_BLINK'] == 0]
    print('\tRemoved {} blink(s)'.format(blink_count))
    return df_new


if __name__ == '__main__':
    args = parse_args()

    resampled_count = 0

    op_start_time = datetime.now()
    directory = os.fsencode(args.dir)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".txt") and not filename.endswith("_processed.txt"):
            file_start_time = datetime.now()

            print('Working on {}:'.format(filename))
            print('\tReading...'.format(filename))
            df = pd.read_csv(os.path.join(args.dir, filename), sep='\t')
            df = manipulate_df(df)

            new_name = os.path.join(args.dir, filename.replace(".txt", "_processed.txt"))
            print('\tExporting...'.format(filename))
            if os.path.isfile(new_name):
                print('\t\tWARNING: Overriding {}'.format(os.path.abspath(new_name)))
            df.to_csv(new_name, sep='\t')
            print('\tExport successful!')
            print('\tTotal {:5f}s'.format((datetime.now() - file_start_time).total_seconds()))
            resampled_count += 1

    print('Operation success: resampled {} dataframe(s) (total {:.5f}s)'.format(resampled_count, (
            datetime.now() - op_start_time).total_seconds()))
