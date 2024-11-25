from random import shuffle, randint
from datetime import datetime
import readline
from os import system, name

from files import *

printable = "abcdefghijklmnopqrstuvwxyząćęłńóśźżABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ ()/-"
"""
Make sure that all the word does not contain nonprintable characters.
"""
def safe_string(s: str):
    return "".join(c for c in s if c in printable)

"""
Check if a voc exists in the current word list. Return None if not found, return the corresponding word if found.
It's an inner function, which means it cannot be accessed by the user.
"""
def check_voc(words: list, voc: str):
    for word in words:
        if word["voc"] == voc:
            return word
    return None

"""
Check if a "meaning" exists in the current word list. 
Return a empty list if not found, return the all corresponding words if found.
It's an inner function, which means it cannot be accessed by the user.
"""
def check_meaning(words: list, meaning: str):
    candidates = []
    for word in words:
        if meaning == word["meaning"] or ("/" + meaning) in word["meaning"] or (meaning + "/") in word["meaning"] or (meaning + "(") in word["meaning"]:
            candidates.append(word)
    return candidates

"""
Update the weight of a word accorrding to the practice result.
It's an inner function, which means it cannot be accessed by the user.
"""
def update_weight(words, word, correct: bool):
    for i in range(len(words)):
        if words[i] == word:
            words[i]["weight"] = max(1, words[i]["weight"] - 2) if correct else words[i]["weight"] + 3

def weighted_sample(words, k):
    shuffle(words)
    weighted_words = sorted(words, key=lambda x: x["weight"], reverse=True)
    return weighted_words[:k]

def load_COMMANDS():
    global COMMANDS, voc_list, meaning_list
    voc_list = [word["voc"] for word in load_words()]
    meaning_list = [word["meaning"] for word in load_words()]
    COMMANDS = {
        "new": ["-b"],
        "list": ["-s"],
        "correct": voc_list,  
        "find": voc_list + meaning_list,  
        "practice": [],
        "analyze": [],
        "help": [],
        "exit": [],
        "save": []
    }

voc_list = []
meaning_list = []
COMMANDS = {}
def completer(text, state):
    buffer = readline.get_line_buffer().split()
    
    if len(buffer) == 0:
        matches = [cmd for cmd in COMMANDS]
    elif len(buffer) == 1:
        matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    elif len(buffer) > 1:
        command = buffer[0]
        argument_text = buffer[1]
        
        if command in COMMANDS:
            matches = [arg for arg in COMMANDS[command] if arg.startswith(argument_text)]
        else:
            matches = []
    else:
        matches = []
    
    # Return the match for the current state
    if state < len(matches):
        return matches[state]
    return None

def add_history_if_command(command: str):
    if command in COMMANDS:
        readline.add_history(command)

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

def clear_screen():
    system('clear' if name == 'posix' else 'cls')

def ctrl_l_handler():
    clear_screen()
    print(">>> ", end='', flush=True)

readline.parse_and_bind('"control-l": clear-screen')

def classify(words, word, _class):
    for i in range(len(words)):
        if words[i] == word:
            words[i]["class"] = _class