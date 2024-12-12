from random import shuffle, randint
from datetime import datetime
import readline
from os import system, name

from files import *

printable = "abcdefghijklmnopqrstuvwxyząćęłńóśźżABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ ()/,-0123456789"

def safe_string(s: str):
    """
    Make sure that all the word does not contain nonprintable characters.
    """
    return "".join(c for c in s if c in printable)

def check_voc(words: list, voc: str):
    """
    Check if a voc exists in the current word list.
    Return None if not found, return the corresponding word if found.
    """
    for word in words:
        if word["voc"] == voc:
            return word
    return None

def check_meaning(words: list, meaning: str):
    """
    Check if a "meaning" exists in the current word list. 
    Return a empty list if not found, return the all corresponding words if found.
    """
    candidates = []
    for word in words:
        if meaning == word["meaning"] or ("/" + meaning) in word["meaning"] or (meaning + "/") in word["meaning"] or (meaning + "(") in word["meaning"]:
            candidates.append(word)
    return candidates

def update_weight(words: list, word: dict, correct: bool):
    """
    Update the weight of a word accorrding to the practice result.
    """
    for i in range(len(words)):
        if words[i] == word:
            words[i]["weight"] = max(1, words[i]["weight"] - 2) if correct else words[i]["weight"] + 3

def weighted_sample(words: list, k):
    """
    Pick k samples from list based on their weights.
    """
    shuffle(words)
    weighted_words = sorted(words, key=lambda x: x["weight"], reverse=True)
    return weighted_words[:k]

def load_COMMANDS(words: list):
    """
    Load the lists for the autocompleter.
    """
    global COMMANDS, voc_list, meaning_list
    voc_list = [word["voc"] for word in words]
    meaning_list = [word["meaning"] for word in words]
    COMMANDS = {
        "new": ["-b"],
        "list": ["-s", "-n", "-v", "-adj", "-adv", "-pron"],
        "correct": voc_list,  
        "find": voc_list + meaning_list,  
        "practice": [],
        "analyze": [],
        "help": [],
        "exit": [],
        "save": [],
        "classify": []
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

def classify_word(words: list, word: dict):
    """
    Classify a word.
    """
    for i in range(len(words)):
        if words[i] == word:
            _class = safe_string(input(f"classify {word["voc"]}: "))
            if _class == "end":
                return False
            words[i]["class"] = _class
            return True