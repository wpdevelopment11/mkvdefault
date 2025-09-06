#!/usr/bin/env python3

"""A wrapper over mkvpropedit to quickly change the default track in an mkv file."""

from functools import reduce

import argparse
import glob
import json
import os
import os.path
import subprocess
import sys

def exit_if_err(proc, err_msg, proc_output):
    if proc.returncode == 0:
        return
    print("{} exited with a non-zero code: {}".format(proc.args[0], proc.returncode))
    print(err_msg)
    print(proc_output.removesuffix("\n"))
    sys.exit(1)

def print_and_exit(message):
    print(message)
    sys.exit(1)

def print_tracks(tracks):
    for track_num, track in tracks:
        name_maxlen = reduce(lambda maxlen, name: max(maxlen, len(name)),
                             [track["properties"]["track_name"] for _, track in tracks if track["properties"].get("track_name")],
                             0)
        default_str = "default" if track["properties"]["default_track"] else ""
        track_name = track["properties"].get("track_name", "")
        print("{:<2}) {:<9} ({}) {:<{}} {}".format(track_num,
                                                   track["type"],
                                                   track["properties"].get("language", "???"),
                                                   track_name,
                                                   name_maxlen,
                                                   default_str))

def tracks_of_type(tracks, track_type=None):
    return [(i+1, track) for i, track in enumerate(tracks)
            if track_type is None or track["type"] == track_type]

def mkvmerge(file):
    proc = proc_run(["mkvmerge", "-J", file])
    mkv_info = json.loads(proc.stdout)
    err_output = "".join(mkv_info["errors"]) + "".join(mkv_info["warnings"])
    exit_if_err(proc, "While trying to identify a file '{}'.".format(file), err_output)
    return mkv_info

def mkvpropedit(file, tracks_to_modify):
    cmd = ["mkvpropedit", file]
    for track_num, default in tracks_to_modify:
        cmd += ["--edit", "track:{}".format(track_num), "--set", "flag-default={:d}".format(default)]
    proc = proc_run(cmd)
    exit_if_err(proc, "While trying to modify a file '{}'.".format(file), proc.stdout)

def proc_run(args):
    return subprocess.run(args, capture_output=True, encoding="utf-8")

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--print", action="store_true", help="Print the tracks before and after modification")
    parser.add_argument("-s", "--same-lang", action="store_true", help="Reset the previous default only if the language is the same")
    parser.add_argument("-t", "--default-type", choices=["audio", "subtitles", "video"], metavar="type", help="Type of the default track. Type can be audio, subtitles, or video")
    parser.add_argument("name_or_number", metavar="name|number", help="Name of the new default track or its number")
    parser.add_argument("files", nargs="*", metavar="file", help="An MKV file in which you want to change the default track. If not provided, the CWD is used to discover files with an .mkv extension")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()

    files, name_or_number = args.files, args.name_or_number

    files = files if files else glob.iglob(os.path.join(os.getcwd(), "**", "*.mkv"), recursive=True)

    if name_or_number.isdecimal():
        def matchfunc(nth_of_type, track):
            return (nth_of_type if args.default_type else track[0]) == name_or_number
        name_or_number = int(name_or_number)
        if name_or_number <= 0:
            print_and_exit("Track numbers starts at 1.")
    else:
        def matchfunc(_, track):
            track = track[1]
            return name_or_number.casefold() in track["properties"].get("track_name", "").casefold()

    for file in files:
        mkv_info = mkvmerge(file)

        if mkv_info["container"]["type"] != "Matroska":
            print_and_exit("The file '{}' is not an MKV file.".format(file))

        tracks = [track for i, track in enumerate(tracks_of_type(mkv_info["tracks"], args.default_type))
                if matchfunc(i+1, track)]
        if len(tracks):
            if len(tracks) > 1:
                # here tracks always have a name
                track_numbers = [i for i, _ in tracks]
                print("Multiple tracks match in file '{}'. Select the track using its number:".format(file))
                while True:
                    print_tracks(tracks)
                    num = input()
                    try:
                        num = int(num)
                        i = track_numbers.index(num)
                        default_track_num, track = tracks[i]
                    except ValueError:
                        print("Invalid track number. Try again!")
                        continue
                    break
            else:
                default_track_num, track = tracks[0]
            default_type = track["type"]
            default_lang = track["properties"].get("language")
            tracks_to_modify = [(i, i == default_track_num)
                            for i, track in tracks_of_type(mkv_info["tracks"], default_type)
                            if ((i != default_track_num and track["properties"]["default_track"]
                                    and (not args.same_lang or track["properties"].get("language") == default_lang))
                                or (i == default_track_num and not track["properties"]["default_track"]))]
        else:
            print("No tracks match in file '{}'.".format(file))
            continue

        if tracks_to_modify:
            mkvpropedit(file, tracks_to_modify)

        # Print result

        if not args.print:
            continue

        prev = tracks_of_type(mkv_info["tracks"], default_type)
        mkv_info = mkvmerge(file)
        current = tracks_of_type(mkv_info["tracks"], default_type)

        print_message = "tracks of type '{}' in file '{}':".format(default_type, file)

        print("Previous {}".format(print_message))
        print_tracks(prev)
        print("Current {}".format(print_message))
        print_tracks(current)
        print()

if __name__ == "__main__":
    main()
