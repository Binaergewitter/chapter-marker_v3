#!/usr/bin/env python3
""" usage: doit INGOTONSPUR [SENDUNGSNUMMER]
"""

import time
import urllib
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath
import os
from docopt import docopt

def guess_sendungsnummer():
    print("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]


def main():
    args = docopt(__doc__)
    bgtnum = args['SENDUNGSNUMMER'] or guess_sendungsnummer()
    folder_name = f"{bgtnum}_chunks"
    print(f"Handling {bgtnum}")
    r = sr.Recognizer()
    min_silence_len=2000
    silence_thresh=-40
    seek_step=10
    file_path = PurePath(args['INGOTONSPUR'])
    print(f"loading {file_path} into RAM")
    f = AudioSegment.from_file(file_path,file_path.suffix[1:])
    print(f"loaded file from {file_path}")

    start = time.time()
    print(f"Start split on silence at {start}")
    splitted = silence.split_on_silence(f,keep_silence=True,silence_thresh=silence_thresh,min_silence_len=min_silence_len,seek_step=seek_step)
    end = time.time()
    time_needed = end-start
    print(f"Finished splitting progress at {end}, took {time_needed}")
    print(f"writing chunks to {folder_name}")
    os.makedirs(folder_name,exist_ok=True)
    for i, audio_chunk in enumerate(splitted, start=1):
            chunk_filename = os.path.join(folder_name, f"chunk{i:04}.wav")
            audio_chunk.export(chunk_filename, format="wav")
            print(chunk_filename)
            # recognize the chunk
    print("finished")




if __name__ == "__main__":
    main()
