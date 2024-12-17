import fasttext
from files import *

words = load_words()
model = fasttext.load_model('cc.pl.300.bin')
def get_voc_vectors():
    vocabulary = []
    for word in words:
        vocabulary.append(word["voc"])

    voc_vectors = {}
    for word in vocabulary:
        voc_vectors[word] = model.get_word_vector(word)

    return voc_vectors

def get_voc_labels():
    voc_labels = {}
    words = load_words()
    for word in words:
        voc, _class = word["voc"], word["class"]
        match _class:
            case 'n':
                label = 0
            case 'v':
                label = 1
            case 'adj':
                label = 2
            case 'adv':
                label = 3
            case _:
                label = 4
        voc_labels[voc] = label
    return voc_labels
