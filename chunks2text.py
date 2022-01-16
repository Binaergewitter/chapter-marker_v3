#!/usr/bin/env python3
""" usage: doit [CHUNKDIR]
"""

import time
import urllib
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath
import os
from docopt import docopt
import json

def guess_sendungsnummer():
    print("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]


def main():
    args = docopt(__doc__)
    folder_name = args['CHUNKDIR'] or f"{guess_sendungsnummer()}_chunks"
    r = sr.Recognizer()

    start = time.time()
    print(f"Start tts at {start} with dir {folder_name} ({len(os.listdir(folder_name))} files)")
    ret = {}
    total_length = 0
    for f in sorted(os.listdir(folder_name)):
        file_path = PurePath(os.path.join(folder_name,f))
        segment = AudioSegment.from_file(file_path,file_path.suffix[1:])
        first_speech = silence.detect_leading_silence(segment,-40,10)
        length = len(segment)

        ret[f] = {
            "text": {},
            "length": length,
            "begin": total_length,
            "begin_speech": total_length + first_speech,
            "speech_offset": first_speech,
        }
        total_length += length
        with sr.AudioFile(str(file_path)) as source:
            # somewhat worse output with this:
            #r.adjust_for_ambient_noise(source)
            audio_listened = r.record(source)

            print(f"Handling file {f}")
            try:
                text = r.recognize_google(audio_listened,language='de-DE')
            except sr.UnknownValueError as e:
                print("Error:", str(e))
                text = ""
            else:
                text = f"{text.capitalize()}. "
                print(" -- :", text)
                # try converting it to text
            ret[f]['text']['google'] = text
            print(ret[f])
            time.sleep(3)
    end = time.time()
    time_needed = end-start
    print(f"Finished tts at {end}, took {time_needed/60} Minutes")
    with open(f"{folder_name.split('_')[0]}.json","w+") as f:
        json.dump(ret,f)




if __name__ == "__main__":
    main()
