# mp4c

A wrapper on top of ffmpeg/ffprobe for replacing/adding chapters in an MP4 file

# Dependencies

Requires ffmpeg to be installed and available on your path. ffprobe is also needed but usually bundled with ffmpeg.

# Installation

Just clone/download the repo and run the python file.

# Usage

## Running the script

There are two ways to run the script:
1. Processing a single file, by providing two parameters: MP4 file name, and the chapters text file. E.g. `python mp4c.py file.mp4 chapters.txt`
2. Processing multiple files, by providing one parameter: the directory containing the MP4 and chapter text files. E.g. `python mp4c.py files`
  - Note that for this mode, the txt file name must match the mp4 name without the file extension. E.g. if the MP4 file is called `myvideo.mp4`, then the chapter text file must be called `myvideo.txt`

Note that currently no error handling is implemented. If the chapter txt is out of order, the behaviour is undefined. If the MP4 is in an unexpected format, the behaviour is undefined. It's recommended to do a test with a copy of your video first!

## Expected files

### MP4 file

Currently only MP4 is supported. Any chapters it has will be removed and replaced by the associated text file containing new chapter information.

### Chapter text file

Each MP4 file provided needs a txt file containing the new chapters for the MP4.
Any invalid lines should be ignored when processing. 
Each line is expected to be in the format: `<time> <title>`

`<title>` is a string representing the name of the chapter. Its end is taken as the first newline.
`<time>` is the timestamp of the start of the chapter. It can be in two formats:
1. `HH:MM:SS` E.g. 1:12:14 which represents 1 hour, 12 minutes, 14 seconds
2. `MM:SS` E.g. 12:14 which represents 12 minutes and 14 seconds