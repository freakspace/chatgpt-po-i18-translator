import os
import sys

import openai
import tiktoken
import polib
from dotenv import load_dotenv

from prices import prices

load_dotenv()

api_key = os.getenv("OPENAPI_KEY")

if not api_key:
    print("No api key found in environment")
    sys.exit()
else:
    openai.api_key = os.environ.get("OPENAPI_KEY")

def generate_messages():
    print("Running..")
    pofile = polib.pofile("django.po")

    messages = []

    for entry in pofile:
        message = {
            "role": "user", 
            "content": f"Please rewrite the following text: {entry.msgstr}"
        }
        messages.append(message)
    
    return messages


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


def complete_chat(messages):
    return openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages
    )


if __name__ == "__main__":

    messages = generate_messages()

    num_tokens = num_tokens_from_messages(messages)

    run = True

    price = num_tokens / 1000 * prices["gpt-3.5-turbo"]

    while run:

        input = input(f"This translation will spend {num_tokens} tokens, equivalent to ${price:.2f}. Do you want to continue? [y/n]")

        if input == "y":
            run = False
            pass
        elif input == "n":
            sys.exit()
        else:
            print("We didn't quite catch that")
        #print(complete_chat(messages))