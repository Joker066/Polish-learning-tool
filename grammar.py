def grammar_noun(voc: str):
    """
    Show all cases of a noun.
    """

    # genetive
    # accusative
    voc_4 = ""
    if voc[-1] == "a":
        voc_4 = voc[:-1] + "ę"
    elif voc[-1] in ["o", "e", "ę", "um"]:
        voc_4 = voc
    else:
        voc_4 = voc

    # instrumental
    voc_5 = ""
    if voc[-1] == "a":
        voc_5 = voc[:-1] + "ą"
    elif voc[-1] in ["o", "e"]:
        voc_5 = voc[:-1] + ("iem" if voc[-2] in ["k", "g"] else "em")
    elif voc[-1] in ["ę", "um"]:
        voc_5 = voc
        
    #locative
    voc_6 = ""

    print("#1", voc)
    print("#2")
    print("#4", voc_4)
    print("#5", voc_5)
    print("#6")

print(grammar_noun(input()))
