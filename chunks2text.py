#!/usr/bin/env python3
"""Convert audio chunks to text using speech recognition."""

import time
import datetime
import urllib
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath
import os
import argparse
import json
import logging
from urllib.error import HTTPError
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("chunks2text")

# Mistral API configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MISTRAL_MODEL_DEFAULT = "voxtral-mini-2602"
MISTRAL_APIKEY = os.environ.get("MISTRAL_APIKEY")

if not MISTRAL_APIKEY:
    log.warning("MISTRAL_APIKEY environment variable not set. Mistral transcription will be disabled.")

# prepare silero

from silero import silero_stt, silero_tts
import torch

device = torch.device('cuda')  # gpu also works, but our models are fast enough for CPU
model_sst, decoder, utils = silero_stt(language='de',version='v4',device=device,jit_model="jit_large")
(read_batch, _ , _, prepare_model_input) = utils  # see function signature for details
# model_tts , _ = silero_tts( language='de',  speaker='v3_de',device=device)

def audioToText(wavfile):
    input = prepare_model_input(read_batch([wavfile]),device=device)
    output = model_sst(input)

    text =""
    for example in output:
        text = text + decoder(example.cpu())
    return text

import whisper
#whisper_model = whisper.load_model("medium")
#whisper_model = whisper.load_model("base")
whisper_model_name = "small"
whisper_model = whisper.load_model(whisper_model_name)

whisper_device = str(next(whisper_model.parameters()).device)
if whisper_device.startswith("cuda"):
    print(f"whisper running on GPU ({whisper_device})")
else:
    print(f"whisper running on CPU ({whisper_device})")

def whisperToText(wavfile):
    return whisper_model.transcribe(wavfile,language="de",fp16=False)["text"]


def mistralToText(wavfile, model=MISTRAL_MODEL_DEFAULT):
    """Transcribe audio using Mistral AI API."""
    if not MISTRAL_APIKEY:
        raise RuntimeError("MISTRAL_APIKEY environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_APIKEY}"
    }
    
    with open(wavfile, 'rb') as audio_file:
        files = {
            'file': (os.path.basename(wavfile), audio_file, 'audio/wav')
        }
        data = {
            'model': model,
            'language': 'de'
        }
        
        response = requests.post(
            MISTRAL_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Mistral API error {response.status_code}: {response.text}")
        
        result = response.json()
        return result.get('text', '')


def guess_sendungsnummer():
    log.info("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]

def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)


def load_metadata(metadata_path):
    """Load existing metadata file if it exists."""
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.warning(f"Could not load metadata file: {e}")
    return None


def save_metadata(metadata_path, metadata):
    """Save metadata file."""
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def is_chunk_processed(metadata, chunk_name):
    """Check if a chunk was successfully processed."""
    if metadata is None:
        return False
    chunks = metadata.get('chunks', {})
    chunk_data = chunks.get(chunk_name, {})
    return chunk_data.get('status') == 'success'


def has_engine_result(metadata, chunk_name, engine_key):
    """Check if a specific engine result exists for a chunk."""
    if metadata is None:
        return False
    chunks = metadata.get('chunks', {})
    chunk_data = chunks.get(chunk_name, {})
    text_data = chunk_data.get('text', {})
    return engine_key in text_data


def main():
    parser = argparse.ArgumentParser(description='Convert audio chunks to text using speech recognition.')
    parser.add_argument('chunkdir', nargs='?', default=None,
                        help='Directory containing audio chunks (default: auto-detect from BGT)')
    parser.add_argument('metadata', nargs='?', default=None,
                        help='Path to metadata JSON file (default: <CHUNKDIR>.json)')
    parser.add_argument('--force', action='store_true',
                        help='Force re-doing TTS for all chunks, ignoring previous results')
    parser.add_argument('--mistral-model', default=MISTRAL_MODEL_DEFAULT,
                        help=f'Mistral model to use for transcription (default: {MISTRAL_MODEL_DEFAULT})')
    args = parser.parse_args()

    folder_name = args.chunkdir or f"{guess_sendungsnummer()}_chunks"
    metadata_path = args.metadata or f"{folder_name}.json"
    force = args.force
    mistral_key= f'mistral-{args.mistral_model}'
    whisper_key = f'whisper-{whisper_model_name}'
    r = sr.Recognizer()

    # Load existing metadata (unless force is set, which clears all previous results)
    metadata = load_metadata(metadata_path)
    if force:
        log.info("Force flag set, clearing all previous results and re-processing all chunks")
        metadata = None

    # Initialize or update metadata structure
    if metadata is None:
        metadata = {
            'status': 'in_progress',
            'run_start': datetime.datetime.now().isoformat(),
            'run_end': None,
            'total_duration_seconds': None,
            'chunks': {},
            'timing': {
                'engines': {}
            }
        }
    else:
        # Update for new run
        metadata['status'] = 'in_progress'
        metadata['run_start'] = datetime.datetime.now().isoformat()
        metadata['run_end'] = None

    start = time.time()
    files = sorted([f for f in os.listdir(folder_name) if f.endswith('.wav')])
    log.info(f"Start tts at {start} with dir {folder_name} ({len(files)} files)")

    # Track engine timing across all chunks
    engine_totals = metadata.get('timing', {}).get('engines', {})
    if whisper_key not in engine_totals:
        engine_totals[whisper_key] = {'total_seconds': 0, 'chunks_processed': 0}
    if mistral_key not in engine_totals:
        engine_totals[mistral_key] = {'total_seconds': 0, 'chunks_processed': 0}

    total_length = 0
    processed_count = 0
    skipped_count = 0

    for f in files:
        file_path = PurePath(os.path.join(folder_name, f))
        segment = AudioSegment.from_file(file_path, file_path.suffix[1:])
        first_speech = round(silence.detect_leading_silence(segment, -40, 10) / 1000, 2)
        length = round(len(segment) / 1000, 2)

        # Determine what needs to be processed per engine
        chunk_exists = f in metadata.get('chunks', {})
        needs_whisper = force or not has_engine_result(metadata, f, whisper_key)
        needs_mistral = MISTRAL_APIKEY and (force or not has_engine_result(metadata, f, mistral_key))
        
        # Skip chunk entirely if all engines already have results
        if not needs_whisper and not needs_mistral:
            log.info(f"Skipping chunk {f}: all engines already have results")
            chunk_data = metadata['chunks'].get(f, {})
            total_length += chunk_data.get('length', length)
            skipped_count += 1
            continue

        chunk_start = time.time()
        
        # Preserve existing chunk data when adding new engine results
        if chunk_exists and not force:
            chunk_data = metadata['chunks'][f].copy()
            chunk_data['updated_at'] = datetime.datetime.now().isoformat()
            # Ensure text and timing dicts exist
            if 'text' not in chunk_data:
                chunk_data['text'] = {}
            if 'timing' not in chunk_data:
                chunk_data['timing'] = {}
        else:
            chunk_data = {
                "status": "in_progress",
                "text": {},
                "length": length,
                "begin": total_length,
                "begin_speech": total_length + first_speech,
                "human_time": str(datetime.timedelta(seconds=(total_length + first_speech))),
                "speech_offset": first_speech,
                "timing": {},
                "processed_at": datetime.datetime.now().isoformat()
            }

        total_length += length

        with sr.AudioFile(str(file_path)) as source:
            # Whisper transcription (only if needed)
            if needs_whisper:
                start_whisper = time.time()
                logging.info(f"Handling file {file_path} with whisper")

                try:
                    text = whisperToText(str(file_path))
                    chunk_data['text'][whisper_key] = text
                    end_whisper = time.time()
                    whisper_duration = round(end_whisper - start_whisper, 2)
                    chunk_data['timing'][whisper_key] = whisper_duration

                    # Update engine totals
                    engine_totals[whisper_key]['total_seconds'] += whisper_duration
                    engine_totals[whisper_key]['chunks_processed'] += 1

                    logging.info(f"whisper: {chunk_data['text'][whisper_key]}")
                    logging.info(f"whisper took {round(whisper_duration)} seconds")

                    chunk_data['status'] = 'success'
                except Exception as e:
                    log.error(f"Error processing {f} with whisper: {e}")
                    chunk_data['status'] = 'error'
                    chunk_data['error'] = str(e)
            else:
                log.info(f"Skipping whisper for {f}: {whisper_key} result already exists")

            # Mistral transcription (only if needed)
            if needs_mistral:
                start_mistral = time.time()
                logging.info(f"Handling file {file_path} with mistral (model: {args.mistral_model})")

                try:
                    text_mistral = mistralToText(str(file_path), model=args.mistral_model)
                    chunk_data['text'][mistral_key] = text_mistral
                    end_mistral = time.time()
                    mistral_duration = round(end_mistral - start_mistral, 2)
                    chunk_data['timing'][mistral_key] = mistral_duration

                    # Update engine totals
                    engine_totals[mistral_key]['total_seconds'] += mistral_duration
                    engine_totals[mistral_key]['chunks_processed'] += 1

                    logging.info(f"mistral: {chunk_data['text'][mistral_key]}")
                    logging.info(f"mistral took {round(mistral_duration)} seconds")

                    # Only set success if not already in error state
                    if chunk_data['status'] != 'error':
                        chunk_data['status'] = 'success'
                except Exception as e:
                    log.error(f"Error processing {f} with mistral: {e}")
                    chunk_data['mistral_error'] = str(e)
            elif MISTRAL_APIKEY:
                log.info(f"Skipping mistral for {f}: {mistral_key} result already exists")

        chunk_end = time.time()
        chunk_data['total_chunk_time_seconds'] = round(chunk_end - chunk_start, 2)

        # Save chunk to metadata
        metadata['chunks'][f] = chunk_data
        metadata['timing']['engines'] = engine_totals

        # Save metadata after each successful chunk
        save_metadata(metadata_path, metadata)
        processed_count += 1
        log.info(f"Saved metadata after processing {f}")

    end = time.time()
    time_needed = end - start

    # Finalize metadata
    metadata['status'] = 'success'
    metadata['run_end'] = datetime.datetime.now().isoformat()
    metadata['total_duration_seconds'] = round(time_needed, 2)
    metadata['total_audio_length_seconds'] = round(total_length, 2)
    metadata['chunks_processed'] = processed_count
    metadata['chunks_skipped'] = skipped_count
    metadata['timing']['engines'] = engine_totals

    save_metadata(metadata_path, metadata)

    log.info(f"Finished tts at {end}, took {time_needed/60:.2f} Minutes")
    log.info(f"Processed: {processed_count}, Skipped: {skipped_count}")

    # Output the chunks data (compatible with previous output)
    output = {k: v for k, v in metadata['chunks'].items()}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
