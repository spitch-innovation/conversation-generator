#!/usr/bin/env python3
import re
import os
import json
import sys
import openai


def generate_conversation(script, language, api_key):
    openai.api_key = api_key

    USER_MESSAGE = (
        "Your goal is to synthesize a one to two minute conversation between a "
        "client and agent or manager.  Please follow the SCRIPT guidelines provided "
        "below and use them to inform the conversation.  It should be realistic, and "
        "representative of a natural, semi-spontaneous interaction. Please output "
        f"the conversation text in the following language: {language}.\n\n"
        f"SCRIPT::\n{script}\n\n"
        "RESPONSE:: Please return ONLY a valid JSON FORMAT object as response. "
        "There should be no commentary.  There should be no other text or content "
        "outside of the valid JSON object.  The format of the object should be:\n\n"
        ' [ {"channel": "1", "text": "TEXT"}, {"channel": "2", "text": "TEXT"}, ...]\n'
        "Finally, note that the object must encode a STEREO conversation with exactly "
        "two channels, no more and no less."
    )
    print("Generating conversation with prompt:")
    print(USER_MESSAGE)
    messages = [
        {
            "role": "system",
            "content": (
                "I'm a call center manager. I'm trying to "
                "synthesize example conversations to help train new agents."
            )
        },
        {
            "role": "user",
            "content": USER_MESSAGE
        }
    ]


    payload = {
        "model": "gpt-4",
        "messages": messages
    }

    response = openai.chat.completions.create(
        model='gpt-4',
        messages=messages
    )
    response = response.model_dump()
    conversation = json.loads(
        response['choices'][0]['message']['content'].strip()
    )

    return conversation

if __name__ == "__main__":
    import argparse

    example = f"{sys.argv[0]} --template tpl.txt"
    parser = argparse.ArgumentParser(description=example)
    parser.add_argument("--template", "-t", help="Conversation guidelines.",
                        required=True)
    parser.add_argument("--language", "-l", help="The target language",
                        default="en-us")
    parser.add_argument("--api_key", "-a", help="openai API key",
                        required=True)
    args = parser.parse_args()

    template = open(args.template).read()
    conversation = generate_conversation(template, args.language, args.api_key)
    with open(f"{args.template}_{args.language}.conversation.json", "w") as ofp:
        print(json.dumps(conversation, indent=2), file=ofp)
