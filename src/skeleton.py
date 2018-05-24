import pandas as pd
import configparser as cp
import sys
import os


def read_config():
    config = cp.ConfigParser()
    config.read("options.ini")
    option = config['DEFAULT']
    return option


directory = os.fsencode(sys.argv[1])
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".txt"):
        df = pd.read_csv(sys.argv[1] + "/" + filename, sep='\t')
        print(df[df['RIGHT_IN_BLINK'] == 1].head())
        break
    else:
        continue

op = read_config()
print(list(op))
