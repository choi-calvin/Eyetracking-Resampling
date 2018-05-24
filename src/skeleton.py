import pandas as pd
import configparser as CP
import sys, os

def read_config():
    Config = CP.ConfigParser()
    Config.read("options.ini")
    option = Config['DEFAULT']
    return option


directory = os.fsencode(sys.argv[1])
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".txt"): 
        df = pd.read_csv(sys.argv[1]+"/"+filename,sep='\t')
        print(df[df['RIGHT_IN_BLINK']==1].head())
        break;
    else:
        continue
op = read_config()
print(list(op))
