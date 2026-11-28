"""Project a pinned private Raphael source into separately readable CGX members."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

SOURCE = "71b9bab248fe0e8d343d425efc0301fc4fdf299a4d551e274881314e0d19de98"

class Dataset(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.payloads = []

    def handle_starttag(self, tag, attrs):
        self.active = tag == "script" and dict(attrs).get("id") == "raphael-dataset"

    def handle_data(self, data):
        if self.active:
            self.payloads.append(data)

    def handle_endtag(self, tag):
        self.active = False

def address(slot):
    if type(slot) is not int or not 0 <= slot <= 173:
        raise ValueError("slot outside review address space")
    digits = []
    for _ in range(5):
        slot, digit = divmod(slot, 3)
        digits.append(str(digit))
    return "".join(reversed(digits))

def populate(library, source):
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE:
        raise ValueError("Raphael source revision requires reconciliation")
    parser = Dataset()
    parser.feed(raw.decode("utf-8-sig"))
    if len(parser.payloads) != 1:
        raise ValueError("expected one embedded dataset")
    data = json.loads(parser.payloads[0])
    sentinel = data["sentinel174"]
    if sentinel != {"empty": True, "mintable": False, "geometry": None}:
        raise ValueError("empty sentinel changed")
    folder = library / "raphael"
    notice_name = "ANTIPRISM_COPYING.txt"
    notice = Path(__file__).with_name(notice_name).read_bytes()
    notice_hash = hashlib.sha256(notice).hexdigest()
    if notice_hash != "60f323899c3d6d08ae74776bc369c24e9c46c242b7798d4b9048280bf5d26663":
        raise ValueError("Antiprism source notice checksum mismatch")
    folder.mkdir()
    (folder / notice_name).write_bytes(notice)
    def member(name, obj):
        (folder/name).write_bytes(json.dumps(obj, ensure_ascii=False, separators=(",",":"),allow_nan=False).encode())
        return "raphael/" + name
    meshes = {}
    rows = []
    for entry in data["entries"]:
        slot = entry["s"]
        key = str(entry["m"])
        mesh = data["meshes"][key]
        if key not in meshes:
            meshes[key] = member("mesh-"+key+".json", mesh)
        rows.append({"slot":slot, "address":address(slot), "id":entry["id"], "name":entry["n"],
                     "role":member("role-"+str(slot)+".json",entry), "mesh":meshes[key]})
    if sorted(row["slot"] for row in rows) != list(range(1,174)) or len(meshes)!=157:
        raise ValueError("role and mesh register changed")
    member("index.json", {"profile":"unispace-private-ternary-review-v1","source_sha256":SOURCE,
        "source_notice":{"path":"raphael/" + notice_name,"sha256":notice_hash},
        "encoding":"Unsigned base 3, five digits, most significant first. Numeric value fits one unsigned byte.",
        "zero":{"address":address(0),"source_sentinel":174,**sentinel},"roles":rows,
        "authority":"local review only","native_admission":False,"physics_verified":False})
