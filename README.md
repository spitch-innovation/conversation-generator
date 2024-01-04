# conversation-generator
Generate and synthesize simulated call center conversations with TTS and ChatGPT

Scripts suitable for utilizing AWS Polly and ChatGPT to generate synthetic stereo
recordings of synthetic call center conversations for experimentation.

There are four steps:

1. Think up a 'script' to describe the synthetic conversation you wish to generate.

2. Generate the conversation in JSON format in your preferred target language.

3. Filter available AWS Polly TTS voices for options in your target language, and select your preferred Ids.

4. Generate a synthetic stereo recording of the conversation.


SETUP:
Your system requires the SoX and ffmpeg utilities to be installed.  For Ubuntu:
```
$ sudo apt-get update
$ sudo apt-get install sox ffmpeg
```

Install the python dependencies:
```
$ pip install -r requirements.txt
```

You will also need to configure AWS console API an Secret keys in your OS.
You will also need a valid openai API key.

EXAMPLE:

1. Review the example template_1.txt for an idea about how to write a 'script'.

2. ```
$   python3 generate_conversation.py \
   -t template_1.txt \
   -a OPENAI_KEY \
   -l en-us

```

3. Review the available TTS voices for en-us and select two:
```
$ ./filter_voices.py -l en-us
[
  {
    "Gender": "Female",
    "Id": "Danielle",
    "LanguageCode": "en-US",
    "SupportedEngines": [
      "neural"
    ]
  },
  {
    "Gender": "Male",
    "Id": "Gregory",
    "LanguageCode": "en-US",
```

4. Generate a synthetic recording, complete with optional overlap:
```
$ ./synthesize_call.py -t template_1.txt_en-us.conversation.json \
   -vid1 Joanna -vid2 Matthew --threshold 0.15 --language en-us
   ...
   stereo-6627b181-22d7-4874-879d-be48bbc1704b_en-us.mp3
```

You can play back the recording to review.
