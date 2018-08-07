# Dataset Resampling Script.

For help, run script with help arguments as such:
```
$ python script.py -h
```
or with the long-form:
```
$ python script.py --help
```

## How to start the script
1. Open the **Terminal**.

2. Go to the directory where the script is stored by
```
cd ~/{Your Directory Path}
```

For example,
```
cd Desktop/DUNCAN/eyetracking/src
```

3. Open **options.ini** and modify the values to configure the script's behaviour.

4. In the terminal,

* Option 1: To re-sample every file that is in the same folder as the script, type "python3 script.py" to run the script.

* Option 2: To re-sample every file in a specific folder add the path to the folder after "script.py" For example,
```
python3 script.py Desktop/DUNCAN/eyetracking/another_folder"
```
* Option 3.1: To re-sample a specific file name/prefix/suffix that is in the same folder as the script, simply modify the FILE_TO_PROCESS field in options.ini and run the script as in **Option 1**.

* Option 3.2: To re-sample a specific file name/prefix/suffix that is  NOT in the same folder as the script, modify the FILE_TO_PROCESS field in options.ini and specify the full path to the folder the file is in after "script.py" like Option 2.

## Credits
Created by Christopher Chow and Calvin Choi.

Designed for use in Duncan Lab, University of Toronto.

Built on Python v3.6.4, pandas v0.22.0.