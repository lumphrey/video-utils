"""
This module is a simple wrapper around ffmpeg. It's main purpose is to simplify the process
of concatenating video files.
"""

import subprocess
import os
import re
import sys
import logging
import click
import yaml
from utils import __version__


class FileInfo:
    def __init__(self, filename, start_ts, end_ts):
        self.filename = filename
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.filename_without_extension, self.extension = os.path.splitext(
            self.filename)
        self.is_trimmed = False


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


def do_trim(file_info: FileInfo, output_name,):
    trim_cmd = ["ffmpeg",
                "-loglevel", "warning",
                "-ss", file_info.start_ts,
                "-i", file_info.filename,
                "-c", "copy", output_name]

    if file_info.end_ts:
        trim_cmd[3:3] = ["-to", file_info.end_ts]

    logging.debug('Trim command args: %s', trim_cmd)
    run = subprocess.run(trim_cmd, check=True)
    file_info.is_trimmed = True
    return run.returncode


def do_trim_from_end(video_to_trim, from_ts, trim_end_secs=None):
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


def write_yaml(data, filename):
    with open(filename, 'w', encoding='UTF8') as file:
        yaml.dump(data, file, sort_keys=False, default_flow_style=False)


def read_yaml(filename):
    with open(filename, 'r', encoding='UTF8') as config_file:
        config_dict = yaml.safe_load(config_file)
    return config_dict


def process_config(config_dict):
    file_list = []

    for file_key, file_config in config_dict['files'].items():
        file_info = FileInfo(
            filename=file_config['name'],
            start_ts=file_config.get('start'),
            end_ts=file_config.get('end')
        )

        logging.info('File %s', file_key)
        logging.info('    Name: %s', file_info.filename)
        logging.info('    Start: %s', file_info.start_ts)
        logging.info('    End: %s', file_info.end_ts)

        if file_info.start_ts or file_info.end_ts:
            do_trim(
                file_info, f"{file_info.filename_without_extension}_trimmed.{file_info.extension}")

        logging.info('Trimmed? %s', file_info.is_trimmed)

        file_list.append(file_info)


@click.command()
@click.version_option(version=__version__)
@click.option('--from', 'from_ts', type=str,
              help="Trim output starting at the given timestamp (HH:MM:SS)")
@click.option('--trim-end', 'trim_end_secs', type=int,
              help="Specify the number of seconds to trim off the end of the output file.")
@click.option('--keep-all-files', is_flag=True,
              help='Keeps all output files. Useful for debugging.')
@click.option('--debug', is_flag=True, help='Enable debug logging.')
@click.option('--generate-config', 'generate_config', is_flag=True)
@click.option('--use-config', 'use_config', is_flag=True)
def main(from_ts, trim_end_secs, keep_all_files, generate_config, use_config, debug):
    """
    Concatenates video files in the current directory.
    """
    log_level = logging.INFO if not debug else logging.DEBUG
    logging.basicConfig(
        level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info('Running version %s', __version__)

    files = collect_files(directory='.', pattern=r"join\d+__.*\.mp4")
    if generate_config:
        yaml_dict = {
            'codec': 'hevc_nvenc',
            'files': {
                index: {'name': filename} for index, filename in enumerate(files)
            }
        }
        write_yaml(yaml_dict, 'concat_config.yml')
        return

    if use_config:
        config_dict = read_yaml('concat_config.yml')
        logging.info("Read config file, contents:")
        logging.info(config_dict)

        os.makedirs('concat', exist_ok=True)
        process_config(config_dict)
        return

    if len(files) == 0:
        logging.warning("No files were processed.")
        sys.exit(0)

    join_filename = 'join.txt'
    write_join_file(join_filename, files)

    output_filename = 'output.mp4'
    concat_cmd_return_code = do_concat(join_filename, output_filename)

    # trim output if specified
    if from_ts:
        trim_cmd_return_code = do_trim_from_end(output_filename,
                                                from_ts,
                                                float(trim_end_secs) if trim_end_secs else None)
    else:
        trim_cmd_return_code = 0

    if concat_cmd_return_code == 0 and trim_cmd_return_code == 0:
        for filename in files:
            os.rename(filename, f"processed_{filename}")
        if not keep_all_files and from_ts:
            os.remove(output_filename)

        os.remove(join_filename)

    else:
        logging.error('Return code: %s{return_code}', concat_cmd_return_code)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
