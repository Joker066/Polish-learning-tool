def grammar_noun(voc: str):
    """
    Show all cases of a noun.
    """

    # instrumental
    voc_5 = ""
    if voc[-1] == "a":
        voc_5 = voc[:-1] + "ą"
    elif voc[-1] in ["o", "e"]:
        voc_5 = voc[:-1] + ("iem" if voc[-2] in ["k", "g"] else "em")
    elif voc[-1] in ["ę", "um"]:
        voc_5 = voc
        
    print("#1:", voc)
    print("#2")
    print("#4")
    print("#5")
    print("#6")
