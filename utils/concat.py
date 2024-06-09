"""
This module is a simple wrapper around ffmpeg. It's main purpose is to simplify the process
of concatenating video files.
"""

import subprocess
import argparse
import os
import re
import sys
import logging
from utils import __version__


def collect_files(directory, pattern):
    """
    Collect files in a directory that match a specified pattern.

    Args:
    - directory (str): The directory path to search for files.
    - pattern (str): The regular expression pattern to match filenames.

    Returns:
    - list: A list of filenames that match the specified pattern.
    """
    regex = re.compile(pattern)
    files = os.listdir(path=directory)
    filtered_files = [f for f in files if regex.match(f)]

    logging.debug('Found files in directory: %s', files)
    logging.debug('Found files to join: %s', filtered_files)
    return filtered_files


def get_video_duration_seconds():
    """
    Uses `ffprobe` to retrieve the duration of the output file.
    """
    duration_run = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", "output.mp4"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    duration = float(duration_run.stdout)
    return duration


def write_join_file(join_filename, files):
    """
    Writes filenames to a text file which ffmpeg uses to determine which video files to
    concatenate.
    """
    with open(join_filename, "w", encoding='UTF8') as join_txt:
        for filename in files:
            logging.info('Adding %s to the process queue.', filename)
            join_txt.write(f"file '{filename}'\n")


def do_concat(join_filename, output_filename):
    """
    Concatenate video files using ffmpeg
    """
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", f"{os.path.join('.', join_filename)}",
        "-vf", "select=concatdec_select",
        "-af", "aselect=concatdec_select,aresample=async=1",
        "-c:a", "aac",
        "-c:v", "hevc_nvenc",  # nvidia nvenc h265 encoder
        "-tag:v", "hvc1",
        "-cq", "0",
        "-profile:v", "main10",
        "-b:v", "50M",
        "-maxrate", "50M",
        "-bufsize", "100M",
        # "-c", "copy",
        output_filename
    ]
    logging.debug('Concatenation command args: %s', ffmpeg_cmd)

    run = subprocess.run(ffmpeg_cmd, check=False)
    return_code = run.returncode
    return return_code


def do_trim(video_to_trim, from_ts, trim_end_secs=None):
    """
    Trim a video.

    Args:
        video_to_trim (str): The name of the file to trim.
        from_ts (str): Video content before this timestamp is cut. HH:MM:SS
        trim_end_secs (float): Number of seconds from the end of the video to cut.
    """
    trim_cmd = ["ffmpeg", "-ss", from_ts, "-i",
                video_to_trim, "-c", "copy", "output_trimmed.mp4"]
    if trim_end_secs:
        duration = get_video_duration_seconds()

        trim_cmd[3:3] = ["-to", str(duration - float(trim_end_secs))]

        logging.debug(
            'Trimming last %s seconds from output (originally %s seconds).', trim_end_secs, duration)

    logging.debug('Trim command args: %s', trim_cmd)

    run = subprocess.run(trim_cmd, check=False)
    return run.returncode


def main():
    """
    Concatenates video files in the current directory.
    """

    parser = argparse.ArgumentParser(
        description="Video splitting/concat utility.")
    parser.add_argument('--from', dest="from_ts", type=str, nargs=1,
                        help="Trim output starting at the given timestamp (HH:MM:SS)")
    parser.add_argument('--trim-end', dest="trim_end_secs", type=str, nargs=1,
                        help="Specify the number of seconds to trim off the end of the output file.")
    parser.add_argument('--keep-all-files', action='store_true',
                        help='Keeps all output files. Useful for debugging.')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging.')
    args = parser.parse_args()

    log_level = logging.INFO if not args.debug else logging.DEBUG
    logging.basicConfig(
        level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info('Running version %s', __version__)

    files = collect_files(directory='.', pattern=r"join\d+__.*\.mp4")
    if len(files) == 0:
        logging.warning("No files were processed.")
        sys.exit(0)

    join_filename = 'join.txt'
    write_join_file(join_filename, files)

    output_filename = 'output.mp4'
    concat_cmd_return_code = do_concat(join_filename, output_filename)

    # trim output if specified
    if args.from_ts:
        trim_cmd_return_code = do_trim(output_filename,
                                       args.from_ts[0],
                                       float(args.trim_end_secs[0]) if hasattr(args, 'trim_end_secs') and args.trim_end_secs else None)
    else:
        trim_cmd_return_code = 0

    if concat_cmd_return_code == 0 and trim_cmd_return_code == 0:
        for filename in files:
            os.rename(filename, f"processed_{filename}")
        if not args.keep_all_files and args.from_ts:
            os.remove(output_filename)

        os.remove(join_filename)

    else:
        logging.error('Return code: %s{return_code}', concat_cmd_return_code)


if __name__ == "__main__":
    main()
