from utility import *
from files import *

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
def practice(words: list, records: list, n=15):
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
Save current words and records to .txt
"""
def save(words: list, records: list):
    update_words(words)
    update_records(records)
    print("All words and records are up to date.")
    
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


