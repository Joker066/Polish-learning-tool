from core.files import load_words, save_words_json, JSON_WORDS_PATH, CASES
from core.grammar import grammar_noun, grammar_adj

def ensure_named_forms(word: dict) -> dict:
    """
    For nouns, ensure word['forms'] exists with named keys for sg+pl.
    If pl values are missing, auto-generate using grammar_noun.
    """
    if str(word.get("class","")).lower() != "n":
        return word

    forms = word.get("forms")
    if not forms:
        g = grammar_noun(word["voc"]) or {}
        sg_src = g.get("sg") or {}
        pl_src = g.get("pl") or {}
        mapping = {1:"NOM", 2:"GEN", 3:"DAT", 4:"ACC", 5:"INST", 6:"LOC"}
        word["forms"] = {
            "sg": {mapping[i]: (sg_src.get(i) or sg_src.get(str(i), "") or "") for i in range(1,7)},
            "pl": {mapping[i]: (pl_src.get(i) or pl_src.get(str(i), "") or "") for i in range(1,7)},
        }
        return word

    missing = []
    for name in CASES:
        if forms.get("sg", {}).get(name) is None:
            forms["sg"][name] = ""
        if forms.get("pl", {}).get(name) in (None, ""):
            missing.append(name)

    if missing:
        g = grammar_noun(word["voc"]) or {}
        mapping = {1:"NOM", 2:"GEN", 3:"DAT", 4:"ACC", 5:"INST", 6:"LOC"}
        inv = {v:k for k,v in mapping.items()}
        pl_src = g.get("pl") or {}
        for name in missing:
            i = inv[name]
            forms["pl"][name] = pl_src.get(i) or pl_src.get(str(i), "") or forms["pl"].get(name, "")

    word["forms"] = {
        "sg": {name: forms["sg"].get(name, "") for name in CASES},
        "pl": {name: forms["pl"].get(name, "") for name in CASES},
    }
    return word

def ensure_adj_forms(word: dict) -> dict:
    """
    For adjectives, ensure word['adj_forms'] exists with named keys:
      - sg_m, sg_f, sg_n
      - pl_mo (męskoosobowy), pl_nmo (non-męskoosobowy)
    Case names follow CASES exactly.
    """
    cls = str(word.get("class", "")).strip().lower().strip(".")
    if cls not in ("adj", "adjective"):
        return word

    idx_to_case = {i: CASES[i-1] for i in range(1, 7)}
    case_to_idx = {name: i for i, name in idx_to_case.items()}

    def _conv_named(subsrc: dict) -> dict:
        return {idx_to_case[i]: (subsrc.get(i) or subsrc.get(str(i), "") or "") for i in range(1, 7)}

    existing = word.get("adj_forms") or {}
    g = grammar_adj(word["voc"]) or {}

    buckets = {}
    for key in ("sg_m", "sg_f", "sg_n", "pl_mo", "pl_nmo"):
        sub = existing.get(key) or {}
        if not sub or any(k not in CASES for k in sub.keys()):
            buckets[key] = _conv_named(g.get(key) or {})
            continue

        filled = {}
        gsrc = g.get(key) or {}
        for name in CASES:
            v = sub.get(name)
            if v in (None, ""):
                i = case_to_idx[name]
                v = gsrc.get(i) or gsrc.get(str(i), "") or ""
            filled[name] = v
        buckets[key] = filled

    word["adj_forms"] = buckets
    return word

def main():
    words = load_words()
    for i, w in enumerate(words):
        w = ensure_named_forms(w)
        w = ensure_adj_forms(w)
        words[i] = w
    save_words_json(words)
    print(f"Regenerated {JSON_WORDS_PATH} with named forms (nouns + adjectives).")

if __name__ == "__main__":
    main()
