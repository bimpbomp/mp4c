import subprocess
import re
from datetime import datetime
import os

def load_chapters(filename):
    temp_filename = "temp-" + datetime.now().strftime("%H%M%S")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", filename, "-f", "ffmetadata", temp_filename])

    with open(temp_filename) as f:
        chapter_strings = re.findall("\[CHAPTER\]\nTIMEBASE=([0-9]+\/[0-9]+)\nSTART=([0-9]+)\nEND=([0-9]+)\ntitle=(.+)", f.read())

    os.remove(temp_filename)

    # format into dicts list
    chapters = []
    for chapter_string in chapter_strings:
        chapter = {
            'timebase': chapter_string[0],
            'start': chapter_string[1],
            'end': chapter_string[2],
            'title': chapter_string[3],
        }
        chapters.append(chapter)

    return chapters

def add_chapter(new_chapter, chapters):
    # find first chapter with end time less than new_chapter start, or start time too...
    # update the existing chapter's end time to be new_chapter's start time
    # if there is another chapter after the existing chapter, update it's start time to be the new_chapter's end time
    # otherwise, ensure new_chapter's end time is the end of the video 
    pass

def format_time(hrs=0, mins=0, secs=0):
    minutes = (hrs * 60) + mins
    seconds = secs + (minutes * 60)
    return (seconds * 1000)

def chapter_to_string(chapter):
    return f"""
[CHAPTER]
TIMEBASE={chapter['timebase']}
START={chapter['start']}
END={chapter['end']}
title={chapter['title']}
"""

def get_duration_millis(filename):
    duration = str(subprocess.check_output(["ffprobe", "-i", filename, "-show_entries", "format=duration", "-v", "quiet"]))
    result = re.search("duration=([0-9]+\.[0-9]+)", duration)
    duration = result.groups()[0]
    duration = int(float(duration))
    return duration * 1000

def write_test_chapters():
    duration = get_duration_millis("AndrewWiltseKneeSliceVol1.mp4")
    with open("FFMETADATAFILE_mod", 'a') as f:
        f.write(format_chapter("1/1000", 0, format_time(0, 1, 30), "Chapter 1"))
        f.write(format_chapter("1/1000", format_time(0, 1, 30), format_time(0, 25, 0), "Chapter 2"))
        f.write(format_chapter("1/1000", format_time(0, 25, 0), duration, "Chapter 3"))

if __name__ == "__main__":
    chapters = load_chapters("OUTPUT.mp4")
    print(chapters)
