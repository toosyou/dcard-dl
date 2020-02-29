# dcard-dl

This is a downloader for ppt.cc & risu.io resources with password in Dcard.

## Description

It will automaticlly detect the password of those encrypted img/mov which have been uploaded to **ppt.cc** or **risu.io** and download them for you!
We've reached about 70% accuracy simpliy use rule based password detection.
This project is still in development stage.

<!-- **WARNING: ppt.cc is disable now due to its unstable server** -->

## Requirement

You will need Python 3.x to run this script.
Packages' version are not specified, these are just what I'm using.
```
requests = "==2.18.4"
beautifulsoup4 = "==4.8.2"
pysocks = "==1.7.1"
```

## Quick start

If you're using `pipenv`, just follow these steps.
```bash
git clone https://github.com/jasperlin1996/dcard-dl.git
cd dcard-dl
pipenv install
pipenv run python dcard.py
```

## Usage

`browse.py` has been deprecated due to code quality and Dcard website's update.
Now, use `dcard.py` instead.

For basic functions, follow the script below.
```python
python3 dcard.py
```

For more details: 
```
usage: dcard.py [-h] [-c | -r RANGE] [-f FOLDER] [-t THREAD]

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

Example:
```bash
python3 dcard.py -c -t 4 -f data/
```

We search from:
* ~~Original Dcard site -- Daily hot posts~~
* Dcard API -- Same as above, but more flexibility
* Deepcard API -- History hot posts

Have fun! :P
