# Manga-Panel-Extractor
A python implementation of a Manga Panel Extractor and a dialogue bubble text eraser.

The text erasor is based on the CRAFT text detector. See [here](https://github.com/clovaai/CRAFT-pytorch) for more information.

## Installation
This code runs on python >= 3.6, use pip to install dependencies:
```
pip3 install -r requirements.txt
```

## Usage
Use the `main.py` script to extract panels from manga pages provided in `folder`.
```
usage: main.py [-h] [-kt] [-minp [1-99]] [-maxp [1-99]] [-f TEST_FOLDER]

Implementation of a Manga Panel Extractor and dialogue bubble text eraser.

optional arguments:
  -h, --help            show this help message and exit
  -kt, --keep_text      Do not erase the dialogue bubble text.
  -minp [1-99], --min_panel [1-99]
                        Percentage of minimum panel area in relation to total page area.
  -maxp [1-99], --max_panel [1-99]
                        Percentage of maximum panel area in relation to total page area.
  -f FOLDER, --folder FOLDER
                        folder path to input manga pages.
                        Panels will be saved to a directory named `panels` in this folder.
```

### Example
```
python3 main.py -f ./images/
```
