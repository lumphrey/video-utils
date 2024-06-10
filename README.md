# FFmpeg Video Processing Wrapper

This module is a simple wrapper around FFmpeg. Its main purpose is to simplify the process of trimming and concatenating video files. It includes functionalities to handle video file information, collect video files based on patterns, trim videos, concatenate videos, and manage configuration through YAML files.

## Features

- **FileInfo Class**: Represents a video file and its intended processing tasks, such as trimming.
- **Video Trimming**: Trim videos based on start and end timestamps.
- **Video Concatenation**: Concatenate multiple video files into a single output file.
- **Configuration Management**: Generate and read YAML configuration files for batch processing.

## Installation

To use this module, ensure you have FFmpeg installed on your system. You can download it from the [official FFmpeg website](https://ffmpeg.org/download.html).

## Usage

### FileInfo Class

The `FileInfo` class holds information about a video file, including its name, start and end timestamps for trimming, and methods for generating trimmed filenames.

### Trimming Videos

To trim a video, use the `do_trim` function. It takes a `FileInfo` object and an output filename, trimming the video based on the start and end timestamps.

Example:
```python
file_info = FileInfo("video.mp4", "00:00:10", "00:00:20")
return_code = do_trim(file_info, "trimmed_video.mp4")
if return_code == 0:
    print("Trimming successful")
```

### Concatenating Videos

To concatenate multiple video files, use the `do_concat` function. It reads filenames from a join file and concatenates them using FFmpeg.

Example:
```python
write_join_file("join.txt", ["video1.mp4", "video2.mp4"])
do_concat("join.txt", "output.mp4")
```

### Configuration Management

Generate a configuration file with details of the videos to process, or read an existing configuration file to process videos as specified.

Example configuration (`concat_config.yml`):
```yaml
codec: hevc_nvenc
files:
  file1:
    name: video1.mp4
    start: 00:00:10
    end: 00:00:20
  file2:
    name: video2.mp4
```

### Main Script

The main script provides command-line options to generate or use a configuration file for video processing.

Usage:
```bash
python main.py --generate-config  # Generates a config file with the current directory's video files
python main.py --use-config       # Processes videos based on the generated config file
```

### CLI Options

- `--debug`: Enable debug logging.
- `--generate-config`: Generate a configuration file based on the current directory's video files.
- `--use-config`: Use an existing configuration file to process videos.

### Example

To run the main script with debug logging enabled:
```bash
python main.py --debug
```

To generate a configuration file:
```bash
python main.py --generate-config
```

To process videos using an existing configuration file:
```bash
python main.py --use-config
```

## Development

### Building
`python setup.py sdist bdist`

## License

This module is licensed under the MIT License.

## Contributing

Contributions are welcome! Please submit issues and pull requests for any improvements or bug fixes.

## Acknowledgments

- [FFmpeg](https://ffmpeg.org/) for the powerful multimedia processing tools.