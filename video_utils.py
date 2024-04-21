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
    parser = argparse.ArgumentParser(description="Video splitting/concat utility.")
    parser.add_argument('--from', dest="from_ts", type=str, nargs=1, help="Trim output starting at the given timestamp (HH:MM:SS)")
    parser.add_argument('--trim-end', dest="trim_end_secs", type=str, nargs=1, help="Specify the number of seconds to trim off the end of the output file.")
    parser.add_argument('--keep-all-files', action='store_true', help='Keeps all output files. Useful for debugging.')
    args = parser.parse_args()

    files = collect_files(directory='.', pattern=r"join\d+__.*\.mp4")
    with open("join.txt", "w") as join_txt:
        for filename in files:
            print("Found " + filename)
            join_txt.write(f"file '{filename}'\n")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", os.path.join(".", "join.txt"),
        "-c", "copy", "output.mp4"
    ]

    run = subprocess.run(ffmpeg_cmd)
    return_code = run.returncode

    # trim output if specified
    if args.from_ts:
        from_ts = args.from_ts[0]


        trim_cmd = ["ffmpeg", "-ss", from_ts, "-i", "output.mp4", "-c", "copy", "output_trimmed.mp4"]
        if args.trim_end_secs:
            duration_run = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", 
                "default=noprint_wrappers=1:nokey=1", "output.mp4"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            duration = float(duration_run.stdout)
            print(f"Output duration: {duration}")

            trim_end_secs = args.trim_end_secs[0]
            trim_cmd_args = ["-to", str(duration - float(trim_end_secs))]
            trim_cmd[3:3] = trim_cmd_args

            print(f"Trim command: {trim_cmd}")

        run = subprocess.run(trim_cmd)
        trim_cmd_return_code = run.returncode
    else:
        trim_cmd_return_code = 0

    if return_code == 0 and trim_cmd_return_code == 0:
        for filename in files:
            os.rename(filename, f"processed_{filename}")
        if not args.keep_all_files:
            os.remove("output.mp4")

    else:
        print(f"Return code: {return_code}")
        if len(files) == 0:
            print("No files were processed.")


if __name__ == "__main__":
    main()
