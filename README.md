# Play Extractor

Minimalistic tool for efficiently trimming a lot of videos! 

<img src="demo.gif">



## Controls

* **Mouse click**: Go to location in video, hold to scrub through
* **W**: place marker
* **S**: delete markers
* **A**: go to previous video
* **D**: go to next video
* **J**: convert videos
* **K**: show shortcuts
* **Ctrl+O**: Open file
* **Ctrl+Shift+O**: Open folder
* **R**: Toggle file list



## Installation

1. Install ffmpeg
2. Make a virtual env and install requirement.txt with pip
3. run script.py with python



## Project status

Succesfully used the program to trim 2000 videos. Worked great, has some minor changes outlined in the todo which needs to be updated before publishing



## TODO

### Needed

- [ ] Show progress when converting videos
- [ ] Fix bug on open file
- [ ] Restore previous session (in case the program fails, annotations are saved in a hidden pickle file)
- [ ] Force overwrite video on conversion
- [ ] Don't convert a video that has already been converted when user press "convert videos" a second time
- [ ] Code cleanup + refactoring + comments

### Nice to have

- [ ] Scaling on toggle file list
- [ ] Better color on file list
- [ ] Clickable play bar
- [ ] Multiple annotations
- [ ] Expose encoder settings in the settings pane
