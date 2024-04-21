import subprocess
import argparse
import os
import re


def collect_files(directory, pattern):
    regex = re.compile(pattern)
    files = os.listdir(path=directory)
    print(files)
    filtered_files = [f for f in files if regex.match(f)]
    print(filtered_files)
    return filtered_files


def main():
    parser = argparse.ArgumentParser(description="File splitting/concat utility.")
    parser.add_argument("--concat", action="store_true", help="Enable concat mode.")
    parser.parse_args()

    files = collect_files(directory='.', pattern=r"join\d+_\d{6}__.*\.mp4")
    with open("join.txt", "w") as join_txt:
        for filename in files:
            print("Found " + filename)
            join_txt.write(f"file '{filename}'\n")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "./join.txt",
        "-c", "copy", "output.mp4"
    ]
    run = subprocess.run(ffmpeg_cmd)
    return_code = run.returncode

    if return_code == 0:
        for filename in files:
            os.rename(filename, f"processed_{filename}")
    else:
        print(return_code)


if __name__ == "__main__":
    main()