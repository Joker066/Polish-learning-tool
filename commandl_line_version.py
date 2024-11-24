from random import randint, shuffle
from datetime import datetime
import readline
from os import system, name

"""
Loads the word list from words.txt
"""
def load_words():
    words = []
    with open("words.txt", "r") as f:
        for word in f.readlines():
            voc, meaning, weight = word.split('_')
            words.append({"voc": voc, "meaning": meaning, "weight": int(weight[:-1])})
    return words

"""
Updates the current word list to words.txt
"""
def update_words(words: list):
    words.sort(key=lambda x: x["voc"])
    with open("words.txt", "w") as f:
        for word in words:
            try:
                f.write(f"{word["voc"]}_{word["meaning"]}_{word["weight"]}\n")
            except:
                continue

"""
Load the records form records.txt
"""
def load_records():
    records = []
    with open("records.txt", "r") as f:
        for record in f.readlines():
            if record == "\n":
                continue
            r_list = record.split("_")
            accuracy = r_list[0]
            wrong_words = r_list[1:-1] if len(r_list) >= 3 else ""
            timestamp = r_list[-1]
            records.append({"accuracy": float(accuracy), "wrong_words": wrong_words, "timestamp": timestamp})
            
    return records

"""
Updates the current records to records.txt
"""
def update_records(records: list):
    with open("records.txt", "w") as f:
        for record in records:
            f.write(f"{record["accuracy"]}")
            for word in record["wrong_words"]:
                f.write(f"_{word}")
            f.write(f"_{record["timestamp"]}\n")

"""
Add a new word, including voc and meaning, to the current word list.
There are two modes, which can be inticated as an argument in the command line.
1. -n: Normal mode. Add one word to the current word list.
2. -b: Bunch mode. Keeps adding words to the current word list until the user enter "end".
"""
def new_word(words: list, mode="n"):
    if mode == "n":
        voc = safe_string(input("new word: "))
        if voc == "end":
            return
        if check_voc(words, voc):
            print(f"{voc} is already contained.")
            return
        meaning = safe_string(input("meaning: "))
        words.append({"voc": voc, "meaning": meaning, "weight": 10})
        print(f"new word {voc} is updated.")
    elif mode == "b":
        while True:
            voc = safe_string(input("new word: "))
            if voc == "end":
                break
            if check_voc(words, voc):
                print(f"{voc} is already contained.")
                continue
            meaning = safe_string(input("meaning: "))
            words.append({"voc": voc, "meaning": meaning, "weight": 10})
            print(f"new word {voc} is updated.")
    load_COMMANDS()

"""
Correct a word in the current word list, return error message if the word does not exist in the list.
This function takes exactly one argument, which is the word needed to be corrected, and needs to be passed throgh command line.
"""
def correct_word(words: list, voc: str):
    cw = check_voc(words, voc)
    if cw is not None:
        words.remove(cw)
        print(f"{voc} is successfully removed.")
        new_word(words)
    else:
        print(f"{voc} does not exist in the list, try \"new\".")
    load_COMMANDS()

"""
List all the words in the current word list.
There are two modes, which can be inticated as an argument in the command line.
1. -n: Normal mode. Shows all words in the word list.
2. -b: Size mode. Shows only the size of the word list.
"""
def list_words(words: list, mode="n"):
    if mode == "n":
        for word in words:
            print(f"{word["voc"]}: {word["meaning"]}")
    elif mode == "s":
        print(f"number of all words: {len(words)}")

"""
Practice.
"""
def practice(words: list, n=15):
    word_list = weighted_sample(words, n)
    accuracy = 0
    wrong_words = []
    for word in word_list:
        question = "voc" if randint(0, 1) else "meaning"
        correct = False
        if question == "voc":
            answer = safe_string(input(f"meaning of {word["voc"]}:\n"))
            if answer == "end":
                return
            correct = len(answer) > 0 and answer in word["meaning"]
            if correct:
                print(f"\033[32mCorrect!\033[0m")
                accuracy += 1
            else:
                print(f"\033[31mWrong, the answer is\033[0m \033[36m{word["meaning"]}\033[0m")
                wrong_words.append(f"{word["voc"]} means {word["meaning"]}")
            update_weight(words, word, correct)
        elif question == "meaning":
            answer = safe_string(input(f"what voc stands for \"{word["meaning"]}\"?\n"))
            if answer == "end":
                return
            correct = answer == word["voc"]
            if correct:
                print(f"\033[32mCorrect!\033[0m")
                accuracy += 1
            else:
                print(f"\033[31mWrong, the answer is\033[0m \033[36m{word["voc"]}\033[0m")
                wrong_words.append(f"{word["voc"]} means {word["meaning"]}")
        
        update_weight(words, word, correct)
        print(40 * "-")

    print(f"\033[36maccuracy: {accuracy}/{n}\033[0m")
    records.append({"accuracy": accuracy / len(word_list), "wrong_words": wrong_words, "timestamp": datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")})

"""
Check if a word is in the current word list.
This function takes exactly one argument, which is the word needed to be checked, and needs to be passed throgh command line.
"""
def find_word(words: list, s: str):
    if (cw_v := check_voc(words, s)) is not None:
        print(f"{cw_v["voc"]}: {cw_v["meaning"]}")
    elif len(cw_m := check_meaning(words, s)) > 0:
        for word in cw_m:
            print(f"{word["voc"]}: {word["meaning"]}")
    else:
        print(f"{s} does not exist in the list.")

"""
Return the records of previous practice.
"""
def analyze(records: list):
    for record in records:
        print(30 * "=")
        print(record["timestamp"].removesuffix("\n"))
        print(f"accuracy: {record["accuracy"] * 100}%")
        print("wrong words:")
        print("\n".join([word for word in record["wrong_words"]]))
    print(30 * "=")

"""
Show the hint of every command.
"""
def show_help():
    print("""
    Available Commands:
    - new [-b]              Add a new word; use '-b' for batch mode.
    - practice <n>          Start a practice session, n is the number of questions.
    - list [-s]             List all words; use '-s' for summary only.
    - correct <word>        Correct an existing word.
    - find <word>           Find and display a word.
    - analyze               Show previous practice records.
    - help                  Display this help message.
    - save                  Save the words and records.
    - exit                  Exit the application.
    """)

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
        if meaning in word["meaning"]:
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

def save(words: list, records: list):
    update_words(words)
    update_records(records)
    print("All words and records are up to date.")

if __name__== "__main__":
    words = load_words()
    records = load_records()
    load_COMMANDS()
    readline.set_auto_history(False)
    while True:
        command = input(">>> ").split()
        if not command:
            continue
        add_history_if_command(command[0])
        mode = command[0]
        if mode == "new":
            if len(command) == 1:
                new_word(words)
            elif len(command) == 2 and command[1] == "-b":
                new_word(words, mode="b")
            else:
                print("wrong argument, try \"help\".")
        elif mode == "practice":
            if len(command) == 1:
                practice(words)
            elif len(command) == 2 and str.isnumeric(command[1]):
                practice(words, n=int(command[1]))
        elif mode == "list":
            if len(command) == 1:
                list_words(words)
            elif len(command) == 2 and command[1] == "-s":
                list_words(words, mode="s")
            else:
                print("wrong argument, try \"help\".")
        elif mode == "correct":
            if len(command) == 3:
                correct_word(words, f"{command[1]} {command[2]}")
            elif len(command) == 2:
                correct_word(words, command[1])
            else:
                print("wrong argument, try \"help\".")
        elif mode == "find":
            if len(command) == 3:
                find_word(words, f"{command[1]} {command[2]}")
            elif len(command) == 2:
                find_word(words, command[1])
            else:
                print("wrong argument, try \"help\".")
        elif mode == "analyze":
            analyze(records)
        elif mode == "help":
            show_help()
        elif mode == "save":
            save(words, records)
        elif mode == "exit":
            break
        else:
            print("command not found.")
    
    update_words(words)
    update_records(records)
