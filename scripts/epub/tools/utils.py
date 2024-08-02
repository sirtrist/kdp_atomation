# Windows
import tkinter as tk
from tkinter import filedialog
from rich.console import Console
from rich.text import Text

console = Console()
# Gpt
from vertexai.language_models import ChatModel, InputOutputTextPair


class Windows:
    def file_path(ext:list = [("All files", "*.*")]):
        #   message for user
        text = Text('a window is open let choose your file', style='bold', justify='center')
        text.stylize('red')
        console.print(text)
        
        root = tk.Tk()
        root.withdraw()
               
        # Ask for file with specified extensions
        directory = filedialog.askopenfilename(filetypes=ext)
               
        return directory
    
    def folder_path():
        #   message for user
        text = Text('a window is open let choose your folder', style='bold', justify='center')
        text.stylize('red')
        console.print(text)
        
        root = tk.Tk()
        root.withdraw()
        directory = filedialog.askdirectory()
        return directory
    
class Reader:
    def keywords_from_txt(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f.readlines() if line.strip()]
        return keywords
    
    def unloop(count):
        if count >= 1:
            return False
        else:
            return True
        
class Gpt:
    def writer(context:str, exemple_input:str, exemple_output:str, input:str):
        chat_model = ChatModel.from_pretrained("chat-bison@001")

        parameters = {
            "temperature": 0.2,
            "max_output_tokens": 1000,  # Limit to 1000 tokens per chunk
            "top_p": 0.95,
            "top_k": 40,
        }

        examples = [
            InputOutputTextPair(
                input_text=exemple_input,
                output_text=exemple_output
            ),
        ]


        while True:
               
            chat = chat_model.start_chat(
                context=context,
                examples=examples,
            )
            
            try: response = chat.send_message(input, **parameters)
            except: return ''
            
            if response.text == exemple_output:
                return ''
            elif response.text.startswith("I'm not able to help with that"):
                context += 'rewrite with censure or new question without problems'
                # print('proute')
                continue
            else:
                return response
                
            print(context)
        # elif response.text == 
        