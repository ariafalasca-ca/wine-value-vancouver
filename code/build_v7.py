"""Builds the presentation page from the template and the deck data.
Run from the submission root or code/: python3 -I code/build_v7.py
Inputs: data/deck_data.json (built by code/data.py in the Part A pipeline) and code/story_template_v7.html.
Output: build/Can You Taste the Price.html (standalone page; should match the submitted "Can You Taste the Price.html")."""
import json, pathlib
CODE = pathlib.Path(__file__).resolve().parent; ROOT = CODE.parent
data = json.dumps(json.load(open(ROOT / "data" / "deck_data.json", encoding="utf-8")), separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
page = (CODE / "story_template_v7.html").read_text(encoding="utf-8").replace("__DATA__", data)
cut = page.index("</style>") + len("</style>")
sa = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
      + page[:cut] + "\n</head>\n<body>\n" + page[cut:] + "\n</body>\n</html>\n")
out = ROOT / "build" / "Can You Taste the Price.html"; out.parent.mkdir(exist_ok=True); out.write_text(sa, encoding="utf-8")
shipped = ROOT / "Can You Taste the Price.html"
print("wrote", out, len(sa), "characters;", ("identical to the submitted page" if shipped.exists() and shipped.read_text(encoding="utf-8") == sa else "differs from the submitted page" if shipped.exists() else ""))
