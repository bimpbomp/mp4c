import subprocess
import re
from datetime import datetime
import os
import sys

# matches a chapter block
CHAPTER_REGEX = "\[CHAPTER\]\nTIMEBASE=([0-9]+\/[0-9]+)\nSTART=([0-9]+)\nEND=([0-9]+)\ntitle=(.+)"

# loads chapters from mp4 file metadata
def load_existing_chapters(filename):
    temp_filename = "temp-chapters-" + datetime.now().strftime("%H%M%S")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", filename, "-f", "ffmetadata", temp_filename])

    with open(temp_filename) as f:
        chapter_strings = re.findall(CHAPTER_REGEX, f.read())

    os.remove(temp_filename)

    # format into dicts list and tuple list
    chapters = []
    raw_chapters = []
    for chapter_string in chapter_strings:
        chapter = {
            'timebase': chapter_string[0],
            'start': chapter_string[1],
            'end': chapter_string[2],
            'title': chapter_string[3],
        }

        chapters.append(chapter)
        raw_chapters.append((chapter['start'], chapter['title']))

    return raw_chapters

# loads chapters from a text file in the format:
# HH:MM:SS Title of chapter
# or
# MM:SS Title of chapter
def load_new_chapters(chapter_filename, delimiter=" - "):
    raw_chapters = []

    with open(chapter_filename) as f:
        for line in f.readlines():
            # split by first space to separate time & title
            line = line.split(delimiter, 1)

            # correct number of arguments present: time & title
            if len(line) == 2:
                start_time = line[0]
                start_time = format_time(start_time)

                # time is valid, so parse title and add to chapters
                if start_time > 0:
                    title = line[1]
                    raw_chapters.append((start_time, title.rstrip()))
    
    return raw_chapters

# format a time from HH:MM:SS into milliseconds
def format_time(time):
    time = time.split(":")

    if len(time) == 2:
        ## interpret as minutes and seconds
        time = format_time_into_millis(0, *time)
    elif len(time) == 3:
        ## interpret as hours, minutes, seconds
        time = format_time_into_millis(*time)
    else:
        time = -1

    return time

# helper function for the above
def format_time_into_millis(hrs, mins, secs):
    try:
        hrs = int(hrs)
        mins = int(mins)
        secs = int(secs)
    except ValueError:
        return -1

    minutes = (hrs * 60) + mins
    seconds = secs + (minutes * 60)
    return (seconds * 1000)

# formats a chapter object into a string in the format expected by ffmpeg
def chapter_to_string(chapter):
    return f"""
[CHAPTER]
TIMEBASE={chapter['timebase']}
START={chapter['start']}
END={chapter['end']}
title={chapter['title']}
"""

# gets the duration of the mp4 file in milliseconds
def get_duration_millis(filename):
    duration = str(subprocess.check_output(["ffprobe", "-i", filename, "-show_entries", "format=duration", "-v", "quiet"]))
    result = re.search("duration=([0-9]+\.[0-9]+)", duration)
    duration = result.groups()[0]
    duration = int(float(duration))
    return duration * 1000

def find_index(text, pattern):
    output = -1
    try:
        output = text.index(pattern)
    except ValueError:
        pass
    return output

def remove_existing_chapters(file_metadata):
    re.sub(CHAPTER_REGEX, "", file_metadata)
    return file_metadata

def format_chapters(raw_chapters, mp4_filename):
    duration = get_duration_millis(mp4_filename)

    chapters = []
    for idx, raw_chapter in enumerate(raw_chapters):
        if idx < len(raw_chapters) - 1:
            end_time = raw_chapters[idx + 1][0]
        else:
            end_time = duration

        chapter = {
            'timebase': '1/1000',
            'start': raw_chapter[0],
            'end': end_time,
            'title': raw_chapter[1]
        }
        chapters.append(chapter)
    
    chapter_string = ""
    for chapter in chapters:
        chapter_string += chapter_to_string(chapter)
        chapter_string += "\n"
    
    return chapter_string

def write_new_metadata_to_file(mp4_filename, new_metadata):
    temp_mp4_filename = "temp-mp4-" + datetime.now().strftime("%H%M%S") + ".mp4"
    temp_meta_filename = "temp-meta-" + datetime.now().strftime("%H%M%S")
    with open(temp_meta_filename, "w") as f:
        f.write(new_metadata)

    subprocess.check_output(["ffmpeg", "-i", mp4_filename, "-i", temp_meta_filename, "-map_chapters", "1", "-codec", "copy", temp_mp4_filename])

    os.remove(mp4_filename)
    os.remove(temp_meta_filename)

    os.rename(temp_mp4_filename, mp4_filename)
    
# replaces any chapters in the mp4 file with the new chapters from the chapter file
def replace_chapters_from_file(mp4_filename, new_chapter_filename):
    raw_chapters = load_existing_chapters(mp4_filename)
    new_raw_chapters = load_new_chapters(new_chapter_filename)

    print("Existing chapters")
    for chapter in raw_chapters:
        print(f"{chapter[0]} {chapter[1]}")

    print("")
    print("New chapters")
    for chapter in new_raw_chapters:
        print(f"{chapter[0]} {chapter[1]}")

    metadata_filename = "temp-" + datetime.now().strftime("%H%M%S")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", mp4_filename, "-f", "ffmetadata", metadata_filename])

    with open(metadata_filename) as f:
        file_metadata = f.read()

    os.remove(metadata_filename)

    index_of_first_chapter = find_index(file_metadata, "[CHAPTER]")

    if index_of_first_chapter > 0:
        file_metadata = remove_existing_chapters(file_metadata)
        chapters = format_chapters(new_raw_chapters, mp4_filename)

        file_metadata = file_metadata[:index_of_first_chapter] + chapters + file_metadata [:index_of_first_chapter:]

        print("")
        print("New metadata")
        print(file_metadata)        
        
        write_new_metadata_to_file(mp4_filename, file_metadata)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        mp4_filename = sys.argv[1]
        chapter_filename = sys.argv[2]

        replace_chapters_from_file(mp4_filename, chapter_filename)
    elif len(sys.argv) == 2:
        files_dir = sys.argv[1]

        valid_files = []

        for filename in os.listdir(files_dir):
            f = os.path.join(files_dir, filename)

            # checking if it is a file
            if os.path.isfile(f):
                filename_noext, extension = filename.split(".")
                chapter_file = os.path.join(files_dir, filename_noext + ".txt")

                # add files in tuple if both an mp4 and txt exist with same name
                if extension == "mp4" and os.path.exists(chapter_file):
                    valid_files.append((f, chapter_file))

        for file in valid_files:
            replace_chapters_from_file(*file)
    else:
        print("Error: Expected 2 arguments: file.mp4 chapters.txt\nOr expected 1 argument: files_directory")
