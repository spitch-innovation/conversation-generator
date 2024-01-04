#!/usr/bin/env python3
import boto3
import subprocess
import json
import os
import sys
import uuid
import ffmpeg
import random

def synthesize_speech(text, voice_id, audio_path):
    polly_client = boto3.client('polly')
    # always pick the neural engine
    response = polly_client.synthesize_speech(
        VoiceId=voice_id,
        OutputFormat='mp3',
        Text=text,
        SampleRate='16000',
        Engine='neural'
    )
    
    with open(audio_path, 'wb') as file:
        file.write(response['AudioStream'].read())

    return audio_path

def get_audio_duration(audio_path):
    print(audio_path)
    try:
        probe = ffmpeg.probe(audio_path)
        duration = float(
            next(stream for stream in probe['streams'] \
                 if stream['codec_type'] == 'audio')['duration']
        )
    except ffmpeg.Error as e:
        print(f'An error occurred: {e.stderr.decode()}')
        raise e
    
    return duration

def create_silence_audio(duration, audio_path):
    # note: AWS polly produces audio at a 22050 sample rate
    print(audio_path)
    try:
        (
            ffmpeg
            .input('anullsrc', format='lavfi', r=16000, channel_layout='mono')
            .output(audio_path, ar='16000', ac='1', t=duration)
            .run(overwrite_output=True, quiet=True)
        )
    except ffmpeg.Error as e:
        print(f'An error occurred: {e.stderr.decode()}')
        raise e

def set_overlap(duration, threshold=0.05):
    max_overlap = min(2.0, duration / 2.0)
    set_overlap = random.random()
    if set_overlap <= threshold:
        mu = (max_overlap + duration) / 2
        sigma = (duration - max_overlap) / 6
        overlap = random.gauss(mu, sigma)
        overlap = max(min(overlap, duration), max_overlap)
        overlap = min(max(overlap, 0.), max_overlap)
        return overlap

    return 0.0
        
def process_conversation(json_data, voice_map, language,
                         threshold=0.05, tmp_dir='./tmp', verbose=False):
    channel_1 = []
    channel_2 = []
    
    uuid_str = str(uuid.uuid4())
    
    os.makedirs(tmp_dir, exist_ok=True)
    print("Generating speech and silence segments...")
    overlap = 0.0
    next_overlap = 0.0
    for idx, entry in enumerate(json_data):
        speech_file = os.path.join(
            tmp_dir, f"speech_{uuid_str}_{idx}.mp3"
        )
        synthesize_speech(entry["text"], voice_map[entry["channel"]], speech_file)

        duration = get_audio_duration(speech_file)
        if idx == 0:
            overlap = set_overlap(duration, threshold=threshold)
        duration = duration - overlap + next_overlap
        next_overlap = -overlap
        # this will reset the overlap either to 0.0 or
        # a value around normal distribution centered at
        # half the duration of the current clip
        overlap = set_overlap(duration, threshold=threshold)
        silence_file = os.path.join(
            tmp_dir,
            f"silence_{uuid_str}_{idx}.mp3"
        )
        create_silence_audio(duration, silence_file)

        # where do we put the silence, speech
        # alternate between ch1 and ch2 each step
        if idx % 2 == 0:
            channel_1.append(speech_file)
            channel_2.append(silence_file)
        else:
            channel_1.append(silence_file)
            channel_2.append(speech_file)

    # Combine all audio files into a stereo wav
    print("Merging segments to generate interleaved channels...")
    channel_1_path = os.path.join(
        tmp_dir,
        f"channel_{uuid_str}_1.mp3"
    )
    channel_1_command = f'sox {" ".join(channel_1)} {channel_1_path}'
    os.system(channel_1_command)
    
    channel_2_path = os.path.join(
        tmp_dir,
        f"channel_{uuid_str}_2.mp3"
    )
    channel_2_command = f'sox {" ".join(channel_2)} {channel_2_path}'
    os.system(channel_2_command)

    print("Generating stereo conversation...")
    stereo_path = f"stereo-{uuid_str}_{language}.mp3"
    os.system(
        " ".join([
            f"sox -M {channel_1_path}",
            channel_2_path,
            stereo_path
        ])
    )
    
    # Cleanup
    print("Cleaning up temporary files...")
    for fname in channel_1:
        if verbose == True:
            print(fname, file=sys.stderr)
        os.remove(fname)
    for fname in channel_2:
        if verbose == True:
            print(fname, file=sys.stderr)
        os.remove(fname)

    if verbose == True:
        print(channel_1_path, file=sys.stderr)
    os.remove(channel_1_path)
    
    if verbose == True:
        print(channel_2_path, file=sys.stderr)
    os.remove(channel_2_path)

    return stereo_path



if __name__ == "__main__":
    import argparse

    example = f"{sys.argv[0]} --template tpl.json"
    parser = argparse.ArgumentParser(description=example)
    parser.add_argument("--template", "-t", help="JSON conversation "
                        "template.", required=True)
    parser.add_argument("--tmp_dir", "-td", help="Temp file dir.",
                        default="./tmp")
    parser.add_argument("--language", "-lc", help="Language code",
                        required=True)
    parser.add_argument("--vid1", "-vid1", help="Voice-id 1: Joanna",
                        default="Joanna")
    parser.add_argument("--vid2", "-vid2", help="Voice-id 2: Matthew",
                        default="Matthew")
    # default is 0.05 or 5% - 5% of clips will have an 'overlap'
    # with the other channel
    parser.add_argument("--threshold", "-l", help="Overlap threshold",
                        default=0.05, type=float) 
    parser.add_argument("--verbose", "-v", help="Verbose mode.",
                        default=False, action="store_true")
    args = parser.parse_args()
    
    template = json.load(open(args.template))

    voice_map = {
        "1": args.vid1,
        "2": args.vid2
    }
    stereo_path = process_conversation(
        template,
        voice_map,
        args.language,
        threshold=args.threshold,
        tmp_dir=args.tmp_dir,
        verbose=args.verbose
    )

    os.system(f"play {stereo_path}")
