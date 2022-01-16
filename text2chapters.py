#!/usr/bin/env python3
""" usage: doit [--offset=OFFSET] [(--override CHAPTER CHUNKID)...] [CHAPTERDATA]

with --override you can force a certain chapter to be on a particular chunkid,
e.g. for fixup, chunkid is an integer and coverts to the respective chunkname

--offset lets you configure the offset for the begin (e.g. when adding the intro)
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
from typing import Union,Any
from datetime import timedelta
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("text2chapters")

@dataclass
class Chapter:
    name: str
    seen: list
    options: list
    mandatory: bool
    confirmed: Union[str,None]
    is_begin: bool
    time: Union[int,None]

class ChapterMarks:
    begin: int # begin time (Halli Hallo)
    current: int # the current time (last timestamp + length), gets set when chapter was found
    chapters: OrderedDict[str, Chapter]
    def __init__(self):
        self.chapters = OrderedDict()
        self.offset = 0



    def add(self,name: str, options: list,mandatory:bool = True,is_begin:bool = False):
        self.chapters[name] = Chapter(name=name,seen=list(),options=options,mandatory=mandatory,confirmed=None,is_begin=is_begin,time=None)

    def find_text(self, chunk:str , chunkdata: dict[str,Any]):
        for chap,v in self.chapters.items():
            for o in v.options:
                for recognizer,text in chunkdata['text'].items():
                    if o in text.lower():
                        if not chunk in v.seen:
                            log.info(f'Found possible match for chapter {chap} in chunk {chunk} as it matched text "{o}"')
                            v.seen.append(chunk)
    def override_chapters(self,override: dict[str,Any]):
        """ override the chapters found """
        for k,v in override.items():
            self.chapters[k].confirmed = v

    def finalize_chapters(self,data: dict[str,Any]):
        for k,chap in self.chapters.items():
            # step 1: confirm the active chapter
            if chap.confirmed:
                log.info(f"Chapter {k} already confirmed at {chap.confirmed}")
            elif chap.seen:
                log.debug(f"Chapter {k} seen at the following locations: {chap.seen}")
                if chap.is_begin:
                    chap.confirmed = chap.seen[0]
                else:
                    for chunk in chap.seen:
                        begin_speech = data[chunk]['begin_speech']
                        if begin_speech <= self.current:
                            log.debug(f"Chapter {k} was found before the previous chapter, ignoring")
                            continue
                        else:
                            chap.confirmed = chunk
                            log.info(f"Confirmed chunk {chunk} for chapter {k}")
                            break
            # step 2: calculates the next times
            if chap.is_begin:
                self.begin = data[chap.confirmed]['begin_speech']
            if chap.confirmed:
                self.current = data[chap.confirmed]['begin_speech']
                chap.time = self.current - self.begin
    def render(self):
        for k,chap in self.chapters.items():
            if chap.time is None:
                log.warning(f"skipping chapter {k}, no plausible chunk found")
                continue
            t = str(timedelta(milliseconds=chap.time) + timedelta(milliseconds=self.offset))
            try:
                front,back = t.split(".",1)
                back = back[0:3]
                t = f"{front}.{back}"
            except:
                t = f"{t}.000"

            print(f"{t} {k}")


m = ChapterMarks()
m.add("Halli Hallo und Herzlich Willkommen",[ "halli hallo", "herzlich willkommen" ],True, True)
m.add("Blast from the Past",[ "blast", "platz von der past" ],False)
m.add("Toter der Woche",["toter","toten der woche"],False)
m.add("Untoter der Woche",["untoten der woche"],False)
m.add("News",["news"],True) # this one is tricky
m.add("Themen",[],False) # no news last time
m.add("Mimimi der Woche",["mimimi"],False)
m.add("Lesefoo",["lesen.to"],False)
m.add("Picks",["picks"],True)
m.add("Ende",[ "passt auf euch auf" ,"habt spaß", "bis zum nächsten mal", "ciao ciao" ],True)

def guess_sendungsnummer():
    log.info("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]


def main():
    args = docopt(__doc__)
    data = json.load(open(args['CHAPTERDATA'] or guess_sendungsnummer() + ".json"))
    override = {}
    for idx,k in enumerate(args['CHAPTER']):
        override[k] = f"chunk{int(args['CHUNKID'][idx]):04d}.wav"
        log.debug("Overriding {k} with {override[k]")

    offset = args['--offset']
    if offset:
        log.info(f"Adding offset of {offset}ms to chaptermarks")
        m.offset = int(args['--offset'])

    for chunk,chunkdata in data.items():
        #print(f"Handling Chunk {chunk}")
        m.find_text(chunk,chunkdata)
    m.override_chapters(override)
    m.finalize_chapters(data)
    m.render()


if __name__ == "__main__":
    main()
