import os
import sys
from typing import Union

import openai
import tiktoken
import polib

from prices import prices

from settings import *


def generate_messages(filename: str, trans_to: str, trans_from: str):
    """ Generate a list of all the messages """
    pofile = polib.pofile(os.path.join("in", filename))

    messages = []

    count_skipped = 0

    for entry in pofile:
        if entry.msgstr == "" or entry.msgstr == entry.msgid:
            message = {
                "role": "user", 
                "content": f"Translate this {trans_from} text to {trans_to}: {entry.msgid} and return only the translated string." # f"Translate the following {trans_from} text to {trans_to}: {entry.msgid}"
            }
            messages.append(message)
        else:
            count_skipped += 1

    print(f"Skipped {count_skipped} messages")
    
    return messages

def translate_messages(filename: str, trans_from: str, trans_to: str, skip_tran: Union[str, None] = None):
    """Loop through the pofile and translate each entry."""
    pofile = polib.pofile(os.path.join("in", filename))
    count = 0
    tokens = 0

    for entry in pofile:
        should_translate = (
            skip_tran != "y" or
            entry.msgstr == "" or
            entry.msgstr == entry.msgid
        )

        if should_translate:
            translated_msg, used_tokens = translate_entry(entry.msgid, trans_from, trans_to)
            entry.msgstr = translated_msg
            count += 1
            tokens += used_tokens

    return count, tokens


def translate_entry(msgid: str, trans_from: str, trans_to: str):
    """Translate one entry"""
    message = {
        "role": "user",
        "content": f"Translate the following text from {trans_from} to {trans_to} and return only the translated string: {msgid}"
    }
    completion = complete_chat(message=message)
    translated_msg = completion["choices"][0]["message"]["content"]
    used_tokens = completion["usage"]["total_tokens"]

    return translated_msg, used_tokens


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
  """Returns the number of tokens used by a list of messages."""
  try:
      encoding = tiktoken.encoding_for_model(model)
  except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")
  if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  else:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")


def complete_chat(message):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[message]
    )
    return completion


if __name__ == "__main__":

    try:
        files = os.listdir("in")
        po_files = [file for file in files if file.lower().endswith(".po")]
    except OSError:
        print("Could not access directory")
        sys.exit()

    if len(po_files) == 0:
        print("There are no files to be translated in /in")
        sys.exit()
    
    # Print the list of files
    print("Select a file to translate")
    instructions = []
    for id, file in enumerate(po_files):
        instructions.append(f"Type {id} to translate {file}")
    
    print("\n".join(instructions))
    file_index = input()

    print("From which language?")
    from_lang = input()
    print("To which language?")
    to_lang = input()
    while True:
        print("Do you want to skip exsiting translations? [y/n]")
        skip_tran = input()
        if skip_tran == "y" or skip_tran == "n":
            break
        else:
            print("We didn't quite catch that..")

    # Calculate tokens
    messages = generate_messages(po_files[int(file_index)], from_lang, to_lang)
    num_tokens = num_tokens_from_messages(messages)

    price = num_tokens / 1000 * prices["gpt-3.5-turbo"]

    while True:
        print(f"""
Translating from {from_lang} to {to_lang} will spend approximately {num_tokens} tokens, equivalent to ${price:.2f}. 

Do you want to continue? [y/n]
        """)

        choice = input()

        if choice == "y":
            count, tokens = translate_messages("django.po", from_lang, to_lang, skip_tran=skip_tran)
            print(f"A total of {count} messages was translated")
            print(f"A total of {tokens} was spent")
            break
        elif choice == "n":
            break
        else:
            print("We didn't quite catch that")