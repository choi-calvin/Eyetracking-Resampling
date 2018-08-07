Dataset Resampling Script.

Created By: Christopher Chow and Calvin Choi
Designed For: use in Duncan Lab, University of Toronto
Built On: Python v3.6.4, pandas v0.22.0

For help, run script with help arguments as such:
    $ python script.py -h
or with the long-form:
    $ python script.py --help

How to start the script
1. Open the terminal

2. Go to the directory where your script is stored by typing "cd ~/your directory path"

for example "cd Desktop/DUNCAN/eyetracking/src"

3. Open the options.ini files and modify each option to modify the way the data is re-sampled (aggregations, re-sampling rate .etc)

4. Go back to the terminal,

Option 1: If you wish to re-sample every file that is in the same folder as the script type "python3 script.py" to start the script

Option 2: If you wish to re-sample every file in a specific folder add the path to the folder after "script.py"

for example: "python3 script.py Desktop/DUNCAN/eyetracking/src"

Option 3.1: If you wish to re-sample a specific file name/prefix/suffix that is in the same folder as the script, simply modify the FILE_TO_PROCESS field in options.ini

Option 3.2: If you wish If you wish to re-sample a specific file name/prefix/suffix that is  NOT in the same folder as the script, modify the FILE_TO_PROCESS field in options.ini and specify the full path to the folder the file is in after "script.py" like Option 2.





