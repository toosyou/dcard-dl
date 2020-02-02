# dcard-dl

This is a downloader for ppt.cc & risu.io resources with password in Dcard.

## Description

It will automaticlly detect the password of those encrypted img/mov which have been uploaded to **ppt.cc** or **risu.io** and download them for you!
We've reached about 70% accuracy simpliy use rule based password detection.
This project is still in development stage
**ppt.cc is disable now due to the unstable server**

## Requirement
```
requests
bs4
```

## Usage

For basic functions, follow the script below.
```python
python3 browse.py
```
For more details: 
```
usage: browse.py [-h] [-c | -r RANGE] [-f FOLDER] [-t THREAD]

optional arguments:
  -h, --help            show this help message and exit
  -c, --current         current Dcard site result
  -r RANGE, --range RANGE
                        set range(use deepcard api) format:
                        YYYY_MM_DD_YYYY_MM_DD
  -f FOLDER, --folder FOLDER
                        set folder path(will auto-generate it for u)
  -t THREAD, --thread THREAD
                        default = 4
```

We search from:
* Original Dcard site -- Daily hot posts
* Dcard API -- Same as above, but more flexibility
* Deepcard API -- History hot posts

Have fun! :P
