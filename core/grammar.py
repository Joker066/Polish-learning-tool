from typing import Dict, Optional
from core.files import save_words_json

VOWELS = FINAL_VOWELS = "aąeęioóuy"
EIGHT_COSSONANT = ("b", "p", "m", "n", "f", "w", "s", "z")
ALTERNATION = {
    "d": "dzie", "t": "cie", "r": "rze", "ł": "le",
    "ka": "ce", "ga": "dze", "ha": "sze", "cha": "sze"
}
HARD_SOUND_NOKG = ("c", "j", "ż", "sz", "cz", "rz", "dż")
SOFT_SOUND_SINGLE = ("ś", "ć", "ź", "ń")  # removed plain 'l' (see note)
SOFT_SOUND_DOUBLE = ("dź", "dzi", "si", "ci", "zi", "ni")
SOFT_SOUND_MAP = {"ś": "si", "ć": "ci", "ź": "zi", "ń": "ni"}  # no 'l' here

def _is_vowel(ch: str) -> bool:
    return ch in VOWELS

def _guess_gender(voc: str) -> str:
    if voc.endswith("a"):
        return "f"
    if voc.endswith(("o", "e", "ę", "um")):
        return "n"
    return "m"

def _strip_final_vowel(voc: str) -> str:
    if voc and voc[-1] in FINAL_VOWELS:
        return voc[:-1]
    return voc

# =========================
#  Nouns
# =========================

def _singular_ins_ending(stem: str) -> str:
    return "iem" if stem.endswith(("k", "g")) else "em"

def _plural_nom_ending(stem: str) -> str:
    if stem.endswith(("k", "g")):
        return "i"
    if stem.endswith(SOFT_SOUND_SINGLE):
        return "e"
    if stem.endswith(SOFT_SOUND_DOUBLE):
        return "e"
    if stem.endswith(HARD_SOUND_NOKG):
        return "e"
    return "i"

def grammar_noun(voc: str, gender: Optional[str] = None, animate: Optional[bool] = None) -> Dict[str, Dict[int, str]]:
    """
    Returns:
      {
        "sg": {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},
        "pl": {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...}
      }
    Heuristics; irregulars are not fully covered by design.
    """
    voc = (voc or "").strip()
    g = (gender or _guess_gender(voc)).lower()
    is_anim = bool(animate) if animate is not None else False

    sg: Dict[int, str] = {}
    pl: Dict[int, str] = {}

    # FEMININE (typically -a)
    if g == "f":
        stem = voc[:-1] if voc.endswith("a") else voc

        # Singular
        # NOM
        sg[1] = voc  
        # GEN
        if voc.endswith("ia"):
            sg[2] = voc[:-2] + "ii"   # e.g., Austria→Austrii (sometimes -i; heuristic)
        elif voc.endswith("ja"):
            sg[2] = voc[:-2] + "ji"   # restauracja→restauracji
        elif stem.endswith(SOFT_SOUND_SINGLE):  # ść
            sg[2] = stem[:-1] + SOFT_SOUND_MAP[stem[-1]]
        elif stem.endswith(("k", "g")):
            sg[2] = stem + "i"
        else:
            sg[2] = stem + "y"
        # DAT
        if voc.endswith("ia"):
            sg[3] = voc[:-2] + "ii"
        elif voc.endswith("ja"):
            sg[3] = voc[:-2] + "ji"
        elif stem and stem[-1] == "l":
            sg[3] = stem + "i"
        elif voc and voc[-1] in SOFT_SOUND_SINGLE:
            sg[3] = voc[:-1] + SOFT_SOUND_MAP[voc[-1]]  # e.g., -ć → -ci
        elif len(voc) >= 2 and voc[-2:] in ALTERNATION:  # -ka/-ga/-ha
            sg[3] = voc[:-2] + ALTERNATION[voc[-2:]]
        elif len(voc) >= 3 and voc[-3:] in ALTERNATION:  # -cha
            sg[3] = voc[:-3] + ALTERNATION[voc[-3:]]
        elif stem and stem[-1] in ALTERNATION:           # -d/-t/-r/-ł (replace last)
            sg[3] = stem[:-1] + ALTERNATION[stem[-1]]
        elif stem and stem[-1] in EIGHT_COSSONANT:
            sg[3] = stem + "ie"
        else:
            sg[3] = stem + "y"
        # ACC
        sg[4] = stem + "ę"
        # INS
        sg[5] = stem + "ą"
        # LOC (same pattern as DAT, but write to #6)
        if voc.endswith("ia"):
            sg[6] = voc[:-2] + "ii"
        elif voc.endswith("ja"):
            sg[6] = voc[:-2] + "ji"
        elif stem and stem[-1] == "l":
            sg[6] = stem + "i"
        elif voc and voc[-1] in SOFT_SOUND_SINGLE:
            sg[6] = voc[:-1] + SOFT_SOUND_MAP[voc[-1]]
        elif len(voc) >= 2 and voc[-2:] in ALTERNATION:
            sg[6] = voc[:-2] + ALTERNATION[voc[-2:]]
        elif len(voc) >= 3 and voc[-3:] in ALTERNATION:
            sg[6] = voc[:-3] + ALTERNATION[voc[-3:]]
        elif stem and stem[-1] in ALTERNATION:
            sg[6] = stem[:-1] + ALTERNATION[stem[-1]]
        elif stem and stem[-1] in EIGHT_COSSONANT:
            sg[6] = stem + "ie"
        else:
            sg[6] = stem + "y"

        # Plural (approximate)
        pl_stem = stem
        # NOM
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[1] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "e"
        else:
            pl[1] = pl_stem + _plural_nom_ending(pl_stem)
        # GEN
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[2] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]]
        else:
            pl[2] = pl_stem
        # DAT
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[3] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "om"
        else:
            pl[3] = pl_stem + "om"
        # ACC
        pl[4] = pl[2] if is_anim else pl[1]            
        # INS
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[5] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "ami"
        else:
            pl[5] = pl_stem + "ami"
        # LOC
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[6] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "ach"
        else:
            pl[6] = pl_stem + "ach"
    # NEUTER (often -o, -e, -ę, -um)
    elif g == "n":
        stem = _strip_final_vowel(voc)

        # Singular
        sg[1] = voc                        # NOM
        sg[2] = voc if voc.endswith("um") else stem + "a"  # GEN
        sg[3] = voc if voc.endswith("um") else stem + "u"  # DAT  (fixed)
        sg[4] = voc                        # ACC = NOM
        sg[5] = stem + _singular_ins_ending(stem)          # INS

        # LOC
        if voc.endswith("um"):
            sg[6] = voc
        elif stem:
            # replace last char(s) for palatalizations
            if stem[-1] in ALTERNATION:
                sg[6] = stem[:-1] + ALTERNATION[stem[-1]]
            elif stem.endswith(EIGHT_COSSONANT):
                sg[6] = stem + "ie"
            else:
                sg[6] = stem + "u"
        else:
            sg[6] = "u"

        # Plural
        if voc.endswith(("o", "e", "ę")):
            pl[1] = stem + "a"
        elif voc.endswith("um"):
            pl[1] = voc[:-2] + "a"
        else:
            pl[1] = stem + "a"
        pl[2] = stem                            # Gen (rough)
        pl[3] = stem + "om"                     # Dat
        pl[4] = pl[1]                           # Acc = Nom
        pl[5] = stem + "ami"                    # Instr
        pl[6] = stem + "ach"                    # Loc

    # MASCULINE (default)
    else:
        stem = _strip_final_vowel(voc) if voc and _is_vowel(voc[-1]) else voc

        # Singular
        # NOM
        sg[1] = voc                              
        # GEN
        if stem.endswith(SOFT_SOUND_SINGLE):
            sg[2] = stem[:-1] + SOFT_SOUND_MAP[stem[-1]] + ("a" if is_anim else "u") 
        else:
            sg[2] = stem + ("a" if is_anim else "u") 
        # DAT  
        if stem.endswith(SOFT_SOUND_SINGLE):
            sg[3] = stem[:-1] + SOFT_SOUND_MAP[stem[-1]] + "owi" # or u
        else:
            sg[3] = stem + "owi" # or u
        # ACC         
        sg[4] = sg[2] if is_anim else sg[1]      
        # INS
        if stem.endswith(SOFT_SOUND_SINGLE):
            sg[5] = stem[:-1] + SOFT_SOUND_MAP[stem[-1]] + "em"
        else:
            sg[5] = stem + _singular_ins_ending(stem)
        # LOC
        if voc and voc[-1] in SOFT_SOUND_SINGLE:
            sg[6] = voc[:-1] + SOFT_SOUND_MAP[voc[-1]] + "e"
        elif stem and stem[-1] in ALTERNATION:
            sg[6] = stem[:-1] + ALTERNATION[stem[-1]]
        elif stem and stem[-1] in EIGHT_COSSONANT:
            sg[6] = stem + "ie"
        else:
            sg[6] = stem + "u"

        # Plural (approximate)
        pl_stem = stem
        # NOM
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[1] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "e"
        else:
            pl[1] = pl_stem + _plural_nom_ending(pl_stem)
        # GEN
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[2] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "ów"
        else:
            pl[2] = pl_stem + "ów"
        # DAT
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[3] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "om"
        else:
            pl[3] = pl_stem + "om"
        # ACC
        pl[4] = pl[2] if is_anim else pl[1]            
        # INS
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[5] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "ami"
        else:
            pl[5] = pl_stem + "ami"
        # LOC
        if pl_stem.endswith(SOFT_SOUND_SINGLE):
            pl[6] = pl_stem[:-1] + SOFT_SOUND_MAP[pl_stem[-1]] + "ach"
        else:
            pl[6] = pl_stem + "ach"

    return {"sg": sg, "pl": pl}

# =========================
#  Adjectives (masculine lemma only)
# =========================

def _adj_stem(voc: str) -> str:
    """
    Lemma is M.SG.NOM (usually ends with -y or -i). Strip that for the stem.
    """
    s = (voc or "").strip()
    return s[:-1] if s.endswith(("y", "i")) else s

def _adj_soft_for_im_ym(stem: str, voc: str) -> bool:
    """
    Decide -im/-ym and -imi/-ymi (M/N sg INS/LOC, pl DAT/INS).
    Soft if:
      - stem ends with a soft single/double,
      - or lemma ends with -i,
      - or stem ends with k/g (treat as 'soft-ie' context).
    """
    if stem.endswith(SOFT_SOUND_SINGLE) or stem.endswith(SOFT_SOUND_DOUBLE):
        return True
    if voc.endswith("i"):
        return True
    if stem.endswith(("k", "g")):
        return True
    return False

def _adj_ie_needed(stem: str, voc: str) -> bool:
    """
    Decide -ie vs -e (N.SG; PL non-m+o NOM) and -ich vs -ych (PL GEN/LOC).
    True when soft singles/doubles, or lemma ends with -i/-gi/-ki/-hi/-chi, or stem ends with k/g.
    """
    if stem.endswith(SOFT_SOUND_SINGLE) or stem.endswith(SOFT_SOUND_DOUBLE):
        return True
    if voc.endswith(("i", "gi", "ki", "hi", "chi")):
        return True
    if stem.endswith(("k", "g")):
        return True
    return False

def _adj_gen_dat_endings(stem: str, voc: str) -> tuple[str, str]:
    """
    Gen/Dat M&N.SG endings.
    Use -iego/-iemu in 'soft-ie' contexts (incl. k/g), else -ego/-emu.
    """
    use_ie = _adj_ie_needed(stem, voc)
    return ("iego" if use_ie else "ego", "iemu" if use_ie else "emu")

# Masculine-personal plural nominative alternations (heuristic)
_MP_NOM_MAP_TWO = {
    "ch": "si",   # cichy → cisi
    "cz": "czy",  # heuristic
    "sz": "szy",  # heuristic
    "rz": "rzy",  # heuristic
}
_MP_NOM_MAP_ONE = {
    "d": "dzi",   # młody → młodzi
    "t": "ci",    # bogaty → bogaci
    "r": "rzy",   # dobry → dobrzy
    "ł": "li",    # miły → mili
    "k": "cy",    # krótki → krótcy
    "g": "dzy",   # drogi → drodzy
}

def _adj_mp_nom(stem: str, soft_ie: bool) -> str:
    """
    Build M.PERS plural NOM; fall back to +i/+y when no rule applies.
    """
    if len(stem) >= 2 and stem[-2:] in _MP_NOM_MAP_TWO:
        return stem[:-2] + _MP_NOM_MAP_TWO[stem[-2:]]
    if stem and stem[-1] in _MP_NOM_MAP_ONE:
        return stem[:-1] + _MP_NOM_MAP_ONE[stem[-1]]
    return stem + ("i" if soft_ie else "y")

def grammar_adj(voc: str, animate: Optional[bool] = None) -> Dict[str, Dict[int, str]]:
    """
    Returns:
      {
        "sg_m":  {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},
        "sg_f":  {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},
        "sg_n":  {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},
        "pl_mo": {1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},   # męskoosobowy
        "pl_nmo":{1: ..., 2: ..., 3: ..., 4: ..., 5: ..., 6: ...},   # non-męskoosobowy
      }
    Heuristics; irregulars are not fully covered by design.
    """
    voc = (voc or "").strip()
    stem = _adj_stem(voc)
    soft_imym = _adj_soft_for_im_ym(stem, voc)
    soft_ie = _adj_ie_needed(stem, voc)
    is_anim = bool(animate) if animate is not None else False

    sg_m: Dict[int, str] = {}
    sg_f: Dict[int, str] = {}
    sg_n: Dict[int, str] = {}
    pl_mo: Dict[int, str] = {}
    pl_nmo: Dict[int, str] = {}

    # Singular (masculine)
    gen_suf, dat_suf = _adj_gen_dat_endings(stem, voc)
    sg_m[1] = voc                                 # NOM
    sg_m[2] = stem + gen_suf                      # GEN
    sg_m[3] = stem + dat_suf                      # DAT
    sg_m[4] = sg_m[2] if is_anim else sg_m[1]     # ACC
    sg_m[5] = stem + ("im" if soft_imym else "ym")# INS
    sg_m[6] = stem + ("im" if soft_imym else "ym")# LOC

    # Singular (feminine)
    sg_f[1] = stem + "a"                          # NOM
    sg_f[2] = stem + "ej"                         # GEN
    sg_f[3] = stem + "ej"                         # DAT
    sg_f[4] = stem + "ą"                          # ACC
    sg_f[5] = stem + "ą"                          # INS
    sg_f[6] = stem + "ej"                         # LOC

    # Singular (neuter)
    sg_n[1] = stem + ("ie" if soft_ie else "e")   # NOM
    sg_n[2] = stem + gen_suf                      # GEN
    sg_n[3] = stem + dat_suf                      # DAT
    sg_n[4] = sg_n[1]                             # ACC
    sg_n[5] = stem + ("im" if soft_imym else "ym")# INS
    sg_n[6] = stem + ("im" if soft_imym else "ym")# LOC

    # Plural (męskoosobowy)
    pl_mo[1] = _adj_mp_nom(stem, soft_ie)         # NOM
    pl_mo[2] = stem + ("ich" if soft_ie else "ych")# GEN
    pl_mo[3] = stem + ("im" if soft_imym else "ym")# DAT
    pl_mo[4] = pl_mo[2]                           # ACC = GEN
    pl_mo[5] = stem + ("imi" if soft_imym else "ymi")# INS
    pl_mo[6] = pl_mo[2]                           # LOC = GEN

    # Plural (non-męskoosobowy)
    pl_nmo[1] = stem + ("ie" if soft_ie else "e") # NOM
    pl_nmo[2] = stem + ("ich" if soft_ie else "ych")# GEN
    pl_nmo[3] = stem + ("im" if soft_imym else "ym")# DAT
    pl_nmo[4] = pl_nmo[1]                         # ACC = NOM
    pl_nmo[5] = stem + ("imi" if soft_imym else "ymi")# INS
    pl_nmo[6] = pl_nmo[2]                         # LOC = GEN

    return {
        "sg_m": sg_m,
        "sg_f": sg_f,
        "sg_n": sg_n,
        "pl_mo": pl_mo,
        "pl_nmo": pl_nmo,
    }
