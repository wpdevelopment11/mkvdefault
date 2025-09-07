# Change the default track in an MKV file

Suppose you have a set of MKV files you want to watch,
for example, you're watching a series with multiple translations.
It's annoying to constantly switch the track to a desired one, if the
default one, chosen by your media player is not the track you want.

Your media player chooses the track to play based on the _default flag_.
If it's set to 1, the player selects it.
Usually there is at least one default track of each type: one for audio, video and subtitles.

You can change the default track using [`mkvpropedit`], but that is not convenient.
You need to specify the new default track using its number, you can't use its name.
Additionally, you need to remove the _default flag_ from the previous default track manually,
again, by specifying its number.

Thus, I present you a small wrapper over [`mkvpropedit`] that simplifies the process
of changing default track in an MKV file. See examples below how to use it.

> **Prerequisite:**
>
> Install [MKVToolNix] and add it to your PATH.

[`mkvpropedit`]: https://mkvtoolnix.download/doc/mkvpropedit.html
[MKVToolNix]: https://mkvtoolnix.download/downloads.html

## Example

Replace `movie.mkv` in the examples below with a path to your MKV file.

To set the second audio track as a default, run:

```bash
./mkvdefault.py -p -t audio 2 movie.mkv
```

To set the _default flag_ to the track which contains "shows" in its name, run:

```bash
./mkvdefault.py -p shows movie.mkv
```

To set the second audio track as a default in all MKV files in the current working directory, run:

```bash
./mkvdefault.py -t audio 2
```

## Usage

```
mkvdefault.py [-h] [-p] [-s] [-t type] name|number [file ...]

Positional arguments:
  name|number           Name of the new default track or its number
  file                  An MKV file in which you want to change the default track. If not provided, the CWD is used to discover files with an .mkv extension

Options:
  -p, --print           Print the tracks before and after modification
  -s, --same-lang       Reset the previous default only if the language is the same
  -t, --default-type type
                        Type of the default track. Type can be audio, subtitles, or video
  -h, --help            Show this help message and exit
```
