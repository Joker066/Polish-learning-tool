from command import *
from files import * 
from utility import *

if __name__== "__main__":
    words = load_words()
    records = load_records()
    load_COMMANDS(words)
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
                practice(words, records)
            elif len(command) == 2 and str.isnumeric(command[1]):
                practice(words, records, n=int(command[1]))
        elif mode == "list":
            if len(command) == 1:
                list_words(words)
            elif len(command) == 2 and command[1] == "-s":
                list_words(words, mode="s")
            elif len(command) == 2 and command[1][1:] in {"n", "v", "adj", "adv", "pron"}:
                list_words(words, _class=command[1][1:])
            elif len(command) == 3 and command[1] == "-s" and command[2][1:] in {"n", "v", "adj", "adv", "pron"}:
                list_words(words, mode="s", _class=command[2][1:])
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
