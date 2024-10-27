import time
import json
import requests
import os
from transformers import AutoTokenizer


class QwenAPI():
    def __init__(self, url):
        self.url = url

        print("loading tokenizer")
        if os.path.exists("/mnt/data/hf_models/gpt2"):
            self.tokenizer = AutoTokenizer.from_pretrained("/mnt/data/hf_models/gpt2")
        else:
            raise Exception("No model path found")
        print("loading tokenizer done")

    def response(self, input_text, max_new_tokens=4096):
        current_time = time.time()
        
        input_text_len = len(self.tokenizer(input_text)['input_ids'])
        print(f"input_text_len: {input_text_len}")
        if input_text_len > 128000:
            print(f"input_text_len: {input_text_len}", "we reduce the input_text_len")
            input_text = input_text[:int(len(input_text)*(128000/input_text_len))]

        url = self.url
        headers = {
            # "Content-Type": "application/json",
            "Authorization": "EMPTY"
        }
        raw_info = {
            "model": "Qwen",
            "messages": [{"role": "user", "content": input_text}],
            "seed": 1024,
            "max_tokens": max_new_tokens
        }

        data = json.dumps(raw_info)
        # print(data)

        try_time = 0
        response = None
        while try_time < 3:
            try_time += 1

            try:
                callback = requests.post(url, headers=headers, data=data, timeout=(10000, 10000))
                print("callback.status_code", callback.status_code)
                print(f"prompt_tokens: {callback.json()['usage']['prompt_tokens']}, total_tokens: {callback.json()['usage']['total_tokens']}, completion_tokens: {callback.json()['usage']['completion_tokens']}")
            except Exception as e:
                print(f"(print in qwenapi.py callback, try_time {try_time}) Error: {e}")
                continue

            try:
                result = callback.json()
                # print(result)
                # print(result.keys())
                response = result['choices'][0]['message']['content']
                # print(response)
                # input()
                break
            except Exception as e:
                print(f"(print in qwenapi.py response, try_time {try_time}) callback: {callback.json()} Error: {e}")
                if "Please reduce the length of the messages" in callback.json()['message']:
                    current_tokne_len = callback.json()['message'].split("However, you requested")[1].split("tokens in the messages, Please")[0].strip()
                    current_tokne_len = int(current_tokne_len)
                    print(f"current_tokne_len: {current_tokne_len}")
                    raw_info = {
                        "model": "Qwen",
                        "messages": [{"role": "user", "content": input_text[:int(len(input_text)*(128000/current_tokne_len))]}],
                        "seed": 1024,
                        "max_tokens": max_new_tokens
                    }
                    data = json.dumps(raw_info)
                continue    

        if response is None:
            raise Exception(f"response is None")

        print("used time in this qwenapi:", (time.time()-current_time)/60, "min")
        return response