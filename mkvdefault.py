import argparse
import json
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+", metavar="file.mkv")
args = parser.parse_args()

for file in args.files:
    proc = subprocess.run(["mkvmerge", "-J", file], capture_output=True)

    mkv_info = json.loads(proc.stdout)

    print(mkv_info["file_name"] + ":")

    tracks = [track for track in mkv_info["tracks"] if track["type"] == "audio"]
    def sort_key(track):
        return (not track["properties"]["default_track"],
                track["properties"]["track_name"])
    tracks.sort(key=sort_key)

    for track in tracks:
        print("{:50} (default: {:d})".format(track["properties"]["track_name"] + " [" + track["properties"]["language"] + "]",
                                             track["properties"]["default_track"]))
