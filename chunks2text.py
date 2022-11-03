#!/usr/bin/env python3
""" usage: doit [CHUNKDIR]
"""

import time
import datetime
import urllib
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath
import os
from docopt import docopt
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("chunks2text")

# prepare silero

from silero import silero_stt, silero_tts
import torch

device = torch.device('cpu')  # gpu also works, but our models are fast enough for CPU
model_sst, decoder, utils = silero_stt(language='de', device=device)
(read_batch, _ , _, prepare_model_input) = utils  # see function signature for details
model_tts , _ = silero_tts( language='de',  speaker='v3_de',device=device)

def audioToText(wavfile):
    input = prepare_model_input(read_batch([wavfile]),device=device)
    output = model_sst(input)

    text =""
    for example in output:
        text = text + decoder(example.cpu())
    return text

import whisper
whisper_model = whisper.load_model("base")

def whisperToText(wavfile):
    return whisper_model.transcribe(wavfile,language="de",fp16=False)["text"]

def guess_sendungsnummer():
    log.info("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]

def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def main():
    args = docopt(__doc__)
    folder_name = args['CHUNKDIR'] or f"{guess_sendungsnummer()}_chunks"
    r = sr.Recognizer()

    start = time.time()
    log.info(f"Start tts at {start} with dir {folder_name} ({len(os.listdir(folder_name))} files)")
    ret = {}
    total_length = 0
    for f in sorted(os.listdir(folder_name)):
        file_path = PurePath(os.path.join(folder_name,f))
        segment = AudioSegment.from_file(file_path,file_path.suffix[1:])
        first_speech = round(silence.detect_leading_silence(segment,-40,10) / 1000,2)
        length = round(len(segment) / 1000,2)

        ret[f] = {
            "text": {},
            "length": length,
            "begin": total_length,
            "begin_speech": total_length + first_speech,
            "human_time": str(datetime.timedelta(seconds=(total_length + first_speech))),
            "speech_offset": first_speech,
        }
        print(ret[f])
        total_length += length
        with sr.AudioFile(str(file_path)) as source:
            # somewhat worse output with this:
            #r.adjust_for_ambient_noise(source)
            
            logging.info(f"Handling file {f} with google translate")
            audio_listened = r.record(source)
            start_google = time.time()
            try:
                text = r.recognize_google(audio_listened,language='de-DE')
            except sr.UnknownValueError as e:
                log.error(f"Error: {e}")
                text = ""
            else:
                text = f"{text.capitalize()}. "
            ret[f]['text']['google'] = text
            log.debug(ret[f])
            end_google = time.time()

            start_silero = time.time()
            logging.info(f"Handling file {file_path} with silero")

            text = audioToText(file_path)
            text = f"{text.capitalize()}. "
            ret[f]['text']['silero'] = text
            end_silero = time.time()

            start_whisper = time.time()
            logging.info(f"Handling file {file_path} with whisper")

            text = whisperToText(str(file_path))
            ret[f]['text']['whisper'] = text
            end_whisper = time.time()
            
            logging.info(f"google : {ret[f]['text']['google']}")
            logging.info(f"google took {round(end_google - start_google)} seconds")
            logging.info(f"silero : {ret[f]['text']['silero']}")
            logging.info(f"silero took {round(end_silero - start_silero)} seconds")
            logging.info(f"whisper: {ret[f]['text']['whisper']}")
            logging.info(f"whisper took {round(end_whisper - start_whisper)} seconds")


    end = time.time()
    time_needed = end-start
    log.info(f"Finished tts at {end}, took {time_needed/60} Minutes")
    print(json.dumps(ret))


if __name__ == "__main__":
    main()
