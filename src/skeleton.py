import pandas as pd
import configparser as cp
import sys
import os
import argparse


def read_config():
    config = cp.ConfigParser()
    config.read("options.ini")
    option = config['DEFAULT']
    return option


def parse_args():
    parser = argparse.ArgumentParser(description='Resample eyetracking data according to parameters.')
    parser.add_argument('dir', help='the directory to scan and apply resampling', nargs='?', default=os.getcwd())
    return parser.parse_args()


op = read_config()
# print(list(op))

args = parse_args()
directory = os.fsencode(args.dir)
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".txt"):
        df = pd.read_csv(args.dir + "/" + filename, sep='\t')
        df = df[df['RIGHT_IN_BLINK'] == 1].head(1)
        df.to_csv(sys.argv[1] + "/" + filename.replace(".txt", "") + "_processed.txt", sep='\t')
        break
    else:
        continue
