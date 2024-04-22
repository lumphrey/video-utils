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

    logging.debug(f'Found files in directory: {files}')
    logging.debug(f'Found files to join: {filtered_files}')
    return filtered_files


def main():

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

    logging.info(f'Running version {__version__}')

    files = collect_files(directory='.', pattern=r"join\d+__.*\.mp4")
    if len(files) == 0:
        logging.warning("No files were processed.")
        sys.exit(0)

    with open("join.txt", "w") as join_txt:
        for filename in files:
            logging.info(f'Adding {filename} to the process queue.')
            join_txt.write(f"file '{filename}'\n")

    # Concatenate video files using ffmpeg
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", f"{os.path.join('.', 'join.txt')}",
        "-c", "copy", "output.mp4"
    ]
    logging.debug(f'Concatenation command args: {ffmpeg_cmd}')

    run = subprocess.run(ffmpeg_cmd)
    return_code = run.returncode

    # trim output if specified
    if args.from_ts:
        from_ts = args.from_ts[0]

        trim_cmd = ["ffmpeg", "-ss", from_ts, "-i",
                    "output.mp4", "-c", "copy", "output_trimmed.mp4"]
        if args.trim_end_secs:
            duration_run = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", "output.mp4"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            duration = float(duration_run.stdout)

            trim_end_secs = args.trim_end_secs[0]
            trim_cmd_args = ["-to", str(duration - float(trim_end_secs))]
            trim_cmd[3:3] = trim_cmd_args

            logging.debug(
                f'Trimming last {trim_end_secs} seconds from output (originally {duration} seconds). ')

        logging.debug(f'Trim command args: {trim_cmd}')

        run = subprocess.run(trim_cmd)
        trim_cmd_return_code = run.returncode
    else:
        trim_cmd_return_code = 0

    if return_code == 0 and trim_cmd_return_code == 0:
        for filename in files:
            os.rename(filename, f"processed_{filename}")
        if not args.keep_all_files and args.from_ts:
            os.remove("output.mp4")

    else:
        logging.error(f'Return code: {return_code}')


if __name__ == "__main__":
    main()
