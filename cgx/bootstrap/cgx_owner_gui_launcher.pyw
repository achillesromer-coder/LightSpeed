"""Windows desktop icon entry: opens the LOCAL CGX owner review GUI.
Does not install software, pair devices, deploy, sign or mint.
"""
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

SERVER=Path(__file__).with_name("cgx_owner_gui_loopback.py")
BUILD=Path(__file__).resolve().parents[3]/"CGX_PREMINT_OWNER_GUI_20261106"
URL="http://127.0.0.1:4174/#objects"

def existing_owned_review_server():
    try:
        with urllib.request.urlopen("http://127.0.0.1:4174/",timeout=1) as response:
            return False
    except urllib.error.HTTPError as error:
        return (error.code==403
            and error.headers.get("Server","").startswith("CGXPrivateReview")
            and error.headers.get("X-Frame-Options","")=="DENY")
    except (OSError,ValueError):
        return False

def main():
    if existing_owned_review_server():
        webbrowser.open(URL)
        return
    if not SERVER.is_file() or not (BUILD/"index.html").is_file():
        return
    flags=getattr(subprocess,"DETACHED_PROCESS",0)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
    subprocess.Popen([sys.executable,str(SERVER),
        "--directory",str(BUILD),"--open-browser"],
        cwd=str(SERVER.parent),close_fds=True,creationflags=flags)

if __name__=="__main__":
    main()
