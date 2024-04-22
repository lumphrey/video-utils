# Video Splitting/Concatenation Utility

This Python script is a utility for splitting or concatenating video files using `ffmpeg`. It provides a command-line interface to specify the start time for trimming, the duration to trim from the end, and whether to keep all output files.

## Usage

```bash
python concat.py [--from FROM_TS] [--trim-end TRIM_END_SECS] [--keep-all-files] [--debug]
```

### Options

- `--from FROM_TS`: Trim output starting at the given timestamp (HH:MM:SS).
- `--trim-end TRIM_END_SECS`: Specify the number of seconds to trim off the end of the output file.
- `--keep-all-files`: Keep all output files. Useful for debugging.
- `--debug`: Enable debug logging.

## Pre-requisites

1. Install Python (version 3.8 or later) from [python.org](https://www.python.org/downloads/).

2. Download and install `ffmpeg` from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system's PATH.

## Example

Concatenate video files in the current directory that match the pattern `join\d+__.*\.mp4`:
```bash
python concat.py
```

Trim the output video starting from 10 seconds and remove 5 seconds from the end:
```bash
python concat.py --from 00:00:10 --trim-end 5
```


## Building
```bash
python setup.py sdist bdist
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
