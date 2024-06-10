"""
This module is a simple wrapper around ffmpeg. It's main purpose is to simplify the process
of concatenating video files.
"""

import subprocess
import os
import re
import logging
import click
import yaml
from utils import __version__


class FileInfo:
    """
    This class exposes attributes describing intended processing tasks for a video file.

    Attributes:
        filename (str): The name of the video file including its extension.
        start_ts (str): The starting timestamp (HH:MM:SS.ss) for the intended video processing task.
        end_ts (str): The ending timestamp (HH:MM:SS.ss) for the intended video processing task.
        filename_without_extension (str): The name of the video file without its extension.
        extension (str): The extension of the video file.
        is_trimmed (bool): A flag indicating whether the video has been trimmed.

    Methods:
        trimmed_video_filename(): Generates the filename for the trimmed video.
    """

    def __init__(self, filename, start_ts, end_ts):
        self.filename = filename
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.filename_without_extension, self.extension = os.path.splitext(
            self.filename)
        self.is_trimmed = False

    def trimmed_video_filename(self):
        """
        Generates the filename for the trimmed video.

        Returns:
            str: The filename for the trimmed video, appending '_trimmed' before the file extension.
        """
        return self.filename_without_extension + "_trimmed." + self.extension


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
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", "output.mp4"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

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
    """
    Trims a video file based on the start and end timestamps provided in the FileInfo object.

    Args:
        file_info (FileInfo): An instance of the FileInfo class containing the video file 
                              information and the start and end timestamps for trimming.
        output_name (str): The name of the output file for the trimmed video.

    Returns:
        int: The return code from the subprocess running the ffmpeg trim command.

    Raises:
        subprocess.CalledProcessError: If the ffmpeg command returns a non-zero exit status.

    Example:
        file_info = FileInfo("video.mp4", 10.0, 20.0)
        return_code = do_trim(file_info, "trimmed_video.mp4")
        if return_code == 0:
            print("Trimming successful")
    """
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
    """
    Processes a configuration dictionary to trim and concatenate video files as specified.

    Args:
        config_dict (dict): A dictionary containing the configuration for processing video files.
                            It should have a 'files' key with file configurations.

    Example structure of `config_dict`:
        {
            "files": {
                "file1": {
                    "name": "video1.mp4",
                    "start": "00:00:00",
                    "end": "00:07:21" 
                },
                "file2": {
                    "name": "video2.mp4"
                }
            }
        }

    The function performs the following tasks:
        1. Iterates over each file configuration in `config_dict['files']`.
        2. Creates a FileInfo object for each file.
        3. Logs the file details.
        4. Trims the file if start or end timestamps are specified.
        5. Appends the trimmed or original filename to the file list.
        6. Concatenates the files if there are more than one in the file list.

    Logging:
        Logs the details of each file and the trimming process.

    Calls:
        do_trim(file_info, output_name): Trims the video file if required.
        write_join_file("join.txt", file_list): Writes the filenames to a join file for concatenation.
        do_concat("join.txt", "output.mp4"): Concatenates the video files into a single output file.
    """
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

        # trim files if required
        if file_info.start_ts or file_info.end_ts:
            do_trim(file_info, file_info.trimmed_video_filename())
            file_list.append(file_info.trimmed_video_filename())
        else:
            file_list.append(file_info.filename)

        # concatenate video files
        if len(file_list) > 1:
            write_join_file("join.txt", file_list)
            do_concat("join.txt", "output.mp4")


@click.command()
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help='Enable debug logging.')
@click.option('--generate-config', 'generate_config', is_flag=True)
@click.option('--use-config', 'use_config', is_flag=True)
def main(generate_config, use_config, debug):
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


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
