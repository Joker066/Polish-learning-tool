"""
Loads the word list from documents/words.txt
"""
def load_words():
    words = []
    with open("documents/words.txt", "r") as f:
        for word in f.readlines():
            voc, meaning, weight, _class = word.split('_')
            words.append({"voc": voc, "meaning": meaning, "weight": int(weight), "class": _class[:-1]})
    return words

"""
Updates the current word list to documents/words.txt
"""
def update_words(words: list):
    words.sort(key=lambda x: x["voc"])
    with open("documents/words.txt", "w") as f:
        for word in words:
            try:
                f.write(f"{word["voc"]}_{word["meaning"]}_{word["weight"]}_{word["class"]}\n")
            except:
                continue

"""
Load the records form documents/records.txt
"""
def load_records():
    records = []
    with open("documents/records.txt", "r") as f:
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
Updates the current records to documents/records.txt
"""
def update_records(records: list):
    with open("documents/records.txt", "w") as f:
        for record in records:
            f.write(f"{record["accuracy"]}")
            for word in record["wrong_words"]:
                f.write(f"_{word}")
            f.write(f"_{record["timestamp"]}\n")
