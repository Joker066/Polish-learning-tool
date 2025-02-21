import csv

def load_words():
    """
    Loads the word list from ../documents/words.txt
    """
    words = []
    with open("../documents/words.txt", "r") as f:
        for word in f.readlines():
            voc, meaning, weight, _class = word.split('_')
            words.append({"voc": voc, "meaning": meaning, "weight": int(weight), "class": _class[:-1]})
    return words

def word_to_CSV():
    words = load_words()
    with open("databases/words.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["voc", "meaning", "class"])
        for word in words:
            writer.writerow([word["voc"], word["meaning"], word["class"]])

word_to_CSV()