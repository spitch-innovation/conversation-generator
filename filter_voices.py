#!/usr/bin/env python3
import boto3
import json
import os
import sys
import random

def filter_voices(lang_code):
    polly_client = boto3.client('polly')
    response = polly_client.describe_voices()

    filtered = []
    for voice in response['Voices']:
        LanguageCode = voice['LanguageCode'].lower()
        # only return neural voices; others are terrible
        if lang_code == '' or LanguageCode == lang_code:
            voice_obj = {
                "Gender": voice['Gender'],
                "Id": voice['Id'],
                "LanguageCode": voice['LanguageCode'],
                "SupportedEngines": voice['SupportedEngines']
            }
            filtered.append(voice_obj)
            
    return filtered

if __name__ == "__main__":
    import argparse

    example = f"{sys.argv[0]} --lang_code en-us"
    parser = argparse.ArgumentParser(description=example)
    parser.add_argument("--lang_code", "-l", help="ISO lang code to "
                        "filter voices.", default='')
    args = parser.parse_args()
    voices = filter_voices(args.lang_code)
    print(json.dumps(voices, indent=2))
