#!/usr/bin/env python3
""" usage: split-voice INGOTONSPUR [SENDUNGSNUMMER] [--force]

Options:
    --force     Force re-splitting even if metadata file exists
"""

import time
import urllib
import json
from datetime import datetime
from pydub import AudioSegment, silence
import speech_recognition as sr
from pathlib import PurePath, Path
import os
from docopt import docopt

METADATA_FILENAME = "split_metadata.json"
# Formats that pydub/ffmpeg can handle natively without issues
SUPPORTED_FORMATS = {'flac', 'wav', 'ogg', 'mp3', 'aac', 'm4a', 'wma', 'aiff'}
# Preferred format for conversion (good quality, widely supported)
CONVERT_TO_FORMAT = 'flac'


def detect_and_convert_if_needed(file_path):
    """
    Detect the audio file format and convert to a supported format if necessary.
    Returns the path to use for processing (original or converted file).
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower().lstrip('.')
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    # Check if format is already supported
    if suffix in SUPPORTED_FORMATS:
        print(f"File format '{suffix}' is supported, no conversion needed")
        return file_path, False  # Return original path, no conversion done
    
    # Need to convert - create converted file in same folder
    converted_filename = file_path.with_suffix(file_path + ".converted.flac")
    
    # Check if converted file already exists
    if converted_filename.exists():
        print(f"Converted file already exists: {converted_filename}")
        return converted_filename, True
    
    print(f"Converting '{suffix}' to '{CONVERT_TO_FORMAT}'...")
    print(f"Loading source file: {file_path}")
    
    try:
        # Load the audio file - pydub will try to detect format
        # For unknown formats, try without specifying format (let ffmpeg detect)
        try:
            audio = AudioSegment.from_file(str(file_path), format=suffix)
        except Exception:
            print(f"Could not load with format '{suffix}', trying auto-detection...")
            audio = AudioSegment.from_file(str(file_path))
        
        print(f"Exporting to: {converted_filename}")
        audio.export(str(converted_filename), format=CONVERT_TO_FORMAT)
        print(f"Conversion complete: {converted_filename}")
        
        return converted_filename, True
        
    except Exception as e:
        raise RuntimeError(f"Failed to convert audio file: {e}")


def guess_sendungsnummer():
    print("Retrieving current bgt show number")
    url = "https://pad.binaergewitter.de/"
    ret = urllib.request.urlopen(url)
    return ret.geturl().split("/")[-1]


def check_existing_split(folder_name):
    """Check if a successful split already exists by looking for metadata file."""
    metadata_path = os.path.join(folder_name, METADATA_FILENAME)
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            # Verify the split was successful
            if metadata.get('status') == 'success':
                # Verify all chunk files still exist
                for chunk in metadata.get('chunks', []):
                    if not os.path.exists(chunk['filename']):
                        print(f"Chunk file missing: {chunk['filename']}, will re-split")
                        return False
                return metadata
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Invalid metadata file: {e}, will re-split")
            return False
    return False


def write_metadata(folder_name, chunks_info, split_duration, source_file):
    """Write the finalization metadata file."""
    metadata = {
        'status': 'success',
        'source_file': str(source_file),
        'completed_at': datetime.now().isoformat(),
        'split_duration_seconds': split_duration,
        'total_chunks': len(chunks_info),
        'chunks': chunks_info
    }
    metadata_path = os.path.join(folder_name, METADATA_FILENAME)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata written to {metadata_path}")
    return metadata


def main():
    args = docopt(__doc__)
    bgtnum = args['SENDUNGSNUMMER'] or guess_sendungsnummer()
    folder_name = f"{bgtnum}_chunks"
    force = args['--force']
    print(f"Handling {bgtnum}")

    # Check if split was already performed successfully
    if not force:
        existing_metadata = check_existing_split(folder_name)
        if existing_metadata:
            print(f"Split already completed successfully on {existing_metadata['completed_at']}")
            print(f"Found {existing_metadata['total_chunks']} chunks, took {existing_metadata['split_duration_seconds']:.2f}s")
            print("Use --force to re-split")
            return

    r = sr.Recognizer()
    min_silence_len=2000
    silence_thresh=-40
    seek_step=10
    original_file_path = Path(args['INGOTONSPUR'])
    
    # Detect format and convert if necessary
    file_path, was_converted = detect_and_convert_if_needed(original_file_path)
    
    print(f"loading {file_path} into RAM")
    f = AudioSegment.from_file(str(file_path), file_path.suffix.lstrip('.').lower())
    print(f"loaded file from {file_path}")

    start = time.time()
    print(f"Start split on silence at {start}")
    splitted = silence.split_on_silence(f,keep_silence=True,silence_thresh=silence_thresh,min_silence_len=min_silence_len,seek_step=seek_step)
    end = time.time()
    time_needed = end-start
    print(f"Finished splitting progress at {end}, took {time_needed}")
    print(f"writing chunks to {folder_name}")
    os.makedirs(folder_name,exist_ok=True)

    # Track chunk information for metadata
    chunks_info = []
    current_position_ms = 0

    for i, audio_chunk in enumerate(splitted, start=1):
            chunk_filename = os.path.join(folder_name, f"chunk{i:04}.wav")
            chunk_duration_ms = len(audio_chunk)
            begin_timestamp_ms = current_position_ms
            end_timestamp_ms = current_position_ms + chunk_duration_ms

            audio_chunk.export(chunk_filename, format="wav")
            print(chunk_filename)

            # Store chunk info
            chunks_info.append({
                'filename': chunk_filename,
                'chunk_number': i,
                'begin_timestamp_ms': begin_timestamp_ms,
                'end_timestamp_ms': end_timestamp_ms,
                'duration_ms': chunk_duration_ms,
                'begin_timestamp_formatted': f"{begin_timestamp_ms // 3600000:02}:{(begin_timestamp_ms // 60000) % 60:02}:{(begin_timestamp_ms // 1000) % 60:02}.{begin_timestamp_ms % 1000:03}",
                'end_timestamp_formatted': f"{end_timestamp_ms // 3600000:02}:{(end_timestamp_ms // 60000) % 60:02}:{(end_timestamp_ms // 1000) % 60:02}.{end_timestamp_ms % 1000:03}"
            })

            current_position_ms = end_timestamp_ms

    # Write finalization metadata
    write_metadata(folder_name, chunks_info, time_needed, original_file_path)
    print("finished")




if __name__ == "__main__":
    main()
