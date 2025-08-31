import argparse
import glob
import json
import os
import os.path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("new_default", metavar="new-default")
parser.add_argument("files", nargs="*", metavar="file.mkv")
args = parser.parse_args()

files, new_default = args.files, args.new_default

files = files if files else glob.iglob(os.path.join(os.getcwd(), "**", "*.mkv"), recursive=True)

if new_default.isdecimal():
    new_default = int(new_default)
    def matchfunc(track_num, track):
        return track_num == new_default
else:
    def matchfunc(track_num, track):
        return (new_default.casefold() in track["properties"]["track_name"].casefold()
                if track["properties"].get("track_name") else False)

for file in files:
    proc = subprocess.run(["mkvmerge", "-J", file], capture_output=True)
    mkv_info = json.loads(proc.stdout)

    tracks = [(i+1, track) for i, track in enumerate(mkv_info["tracks"]) if matchfunc(i+1, track)]
    if len(tracks) > 1:
        print("Multiple tracks match")
        exit(1)
    elif len(tracks):
        default_track_num, track = tracks[0]
        default_type = track["type"]
        tracks_to_modify = [(i+1, i+1 == default_track_num)
                         for i, track in enumerate(mkv_info["tracks"])
                         if track["type"] == default_type and ((i+1 != default_track_num and track["properties"]["default_track"])
                                                            or (i+1 == default_track_num and not track["properties"]["default_track"]))]
    else:
        print("No tracks match")
        exit(1)

    cmd = ["mkvpropedit", file]

    if tracks_to_modify:
        for track_num, default in tracks_to_modify:
            cmd += ["--edit", "track:{}".format(track_num), "--set", "flag-default={:d}".format(default)]

        proc = subprocess.run(cmd, capture_output=True)

        if proc.returncode:
            print("mkvpropedit Non-zero exit code: {}".format(proc.returncode))

    # Print result

    proc = subprocess.run(["mkvmerge", "-J", file], capture_output=True)
    mkv_info = json.loads(proc.stdout)

    tracks = [track for track in mkv_info["tracks"] if track["type"] == default_type]

    def sort_key(track):
        props = track["properties"]
        track_name = props["track_name"] if props.get("track_name") else ""
        is_default = props["default_track"]
        return (not is_default, track_name)

    tracks.sort(key=sort_key)

    print(os.path.basename(file))
    for track in tracks:
        props = track["properties"]
        track_name = props["track_name"] if props.get("track_name") else ""
        is_default = props["default_track"]
        print("{:50} (default: {:d})".format(track_name, is_default))
    print()
