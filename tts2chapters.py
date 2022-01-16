#!/usr/bin/env python3
""" usage: doit [(--override CHAPTER CHUNKID)...] [CHAPTERDATA]

with --override you can force a certain chapter to be on a particular chunkid,
e.g. for cleanup
"""

import time
import urllib
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath
import os
from docopt import docopt
import json
from collections import OrderedDict
from dataclasses import dataclass
from typing import Union

@dataclass
class Chapter:
    seen: list
    options: list
    mandatory: bool
    confirmed: Union[int,None]

class ChapterMarks(OrderedDict):
    begin: int # begin time (Halli Hallo)
    def add(self,name: str, options: list,mandatory:bool = True):
        self[name] = Chapter(seen=[],options=options,mandatory=mandatory,confirmed=None)
    def render():
        print("lol")

m = ChapterMarks()
m.add("Begin",[ "Halli hallo", "herzlich willkommen" ])
m.add("Blast from the Past",[ "Blast", "platz von der past" ])
m.add("Toter der Woche",["toter""toten der woche"])
m.add("Untoter der Woche",["untoten der woche"])
m.add("News",["news"]) # this one is tricky
m.add("Themen",[]) # no news last time
m.add("Mimimi der Woche",["mimimi"])
m.add("Lesefoo",["lesen.to"])
m.add("Picks",["picks"])


m["Ende"] = [ "passt auf euch auf" ,"habt spaß", "bis zum nächsten mal", "ciao ciao" ]

def guess_sendungsnummer():
    print("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]


def main():
    args = docopt(__doc__)
    print(args)
    folder_name = args['CHUNKDIR'] or f"{guess_sendungsnummer()}_chunks"
    name = folder_name.split("_")[0]
    r = sr.Recognizer()

    start = time.time()
    print(f"Start tts at {start} with dir {folder_name} ({len(os.listdir(folder_name))} files)")
    ret = {}
    for f in sorted(os.listdir(folder_name)):
        with sr.AudioFile(os.path.join(folder_name,f)) as source:
            audio_listened = r.record(source)
            # try converting it to text
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
            ret[f] = text
            time.sleep(3)
    end = time.time()
    time_needed = end-start
    print(f"Finished tts at {end}, took {time_needed/60} Minutes")
    with open("{name}.json","w+") as f:
        print("Writing to {name}.json")
        json.dump(ret,f)




if __name__ == "__main__":
    main()
