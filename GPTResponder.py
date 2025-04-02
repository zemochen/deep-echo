import os
from openai import OpenAI

import LlmClient as llmClient

from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time

def generate_response_from_transcript(transcript):
    try:
        response = llmClient.request_volce_engine(create_prompt(transcript))

    except Exception as e:
        print(e)
        return ''
    full_response = response.choices[0].message.content
    try:
        return full_response.split('[')[1].split(']')[0]
    except:
        return ''
    
class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()

                transcriber.transcript_changed_event.clear() 
                transcript_string = transcriber.get_transcript()
                print(transcript_string)
                response = generate_response_from_transcript(transcript_string)
                
                end_time = time.time()  # Measure end time
                execution_time = end_time - start_time  # Calculate the time it took to execute the function
                
                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval