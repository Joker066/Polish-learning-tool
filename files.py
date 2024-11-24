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
