# dcard-dl

This is a downloader for ppt.cc resources with password in Dcard.

## Description

It will automaticlly detect the password of those encrypted img/mov which have been uploaded to ppt.cc and download them for you!
We've reached about 70% accuracy simpliy use rule based password detection.
This project is still in development stage

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
Modify `folder` in `browse.py` for changing download folder.
Modify `test_dl_all_img` function for changing the article sourse.
We provide three types of article sourse.

* Original Dcard site -- Daily hot posts
* Dcard API -- Same as above, but more flexibility
* Deepcard API -- History hot posts

If you're using Deepcard API for the article sourse, go to `deepcard.py` and
manually(:P) change the range of the history data.
