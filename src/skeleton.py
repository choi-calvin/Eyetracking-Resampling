import pandas as pd
import configparser as cp
import os
import argparse


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
    df_new = df_old[df_old['RIGHT_IN_BLINK'] == 1].head(1)
    return df_new


if __name__ == '__main__':
    args = parse_args()

    resampled_count = 0

    directory = os.fsencode(args.dir)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".txt") and not filename.endswith("_processed.txt"):
            df = pd.read_csv(os.path.join(args.dir, filename), sep='\t')
            df = manipulate_df(df)

            new_name = os.path.join(args.dir, filename.replace(".txt", "_processed.txt"))
            if os.path.isfile(new_name):
                print('WARNING: Overriding {}'.format(new_name))
            df.to_csv(new_name, sep='\t')
            resampled_count += 1

    print('Operation success: resampled {} dataframe(s)'.format(resampled_count))
