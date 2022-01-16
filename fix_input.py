#!/bin/sh

import json
import sys
import os
import os.path
from pathlib import PurePath
from pydub import AudioSegment, silence

inp = json.load(open(sys.argv[1]))
folder_name = sys.argv[2]
total_length = 0
out = {}
for k,v in inp.items():
    file_path = PurePath(os.path.join(folder_name,k))
    f = AudioSegment.from_file(file_path,file_path.suffix[1:])
    length = len(f)
    first_speech = silence.detect_leading_silence(f,-40,10)
    ret = {
        "tts": {},
        "length": length,
        "begin": total_length,
        "begin_speech": total_length + first_speech,
        "speech_offset": first_speech,
    }
    ret["tts"] = { "google": v }
    out[k] = ret
    print(ret)

json.dump(out,open(sys.argv[1],"w"))
