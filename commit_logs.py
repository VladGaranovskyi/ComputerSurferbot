#!/usr/bin/env python3
import os
import subprocess
import time
import random
import string
from datetime import date, datetime, timedelta

# ---------- Config ----------
START_DATE = date(2023, 12, 1)      # inclusive
TEXT_FILE = "notes.txt"             # file to touch
# ----------------------------

def random_string(n=50):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def ensure_file_exists(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("")

def append_random_char(path):
    ch = random.choice(string.ascii_letters + string.digits)
    with open(path, "a", encoding="utf-8") as f:
        f.write(ch + "\n")

def run_git(args, env=None):
    subprocess.run(["git", *args], check=True, env=env)

def commit_with_date(commit_date_iso, msg):
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date_iso
    env["GIT_COMMITTER_DATE"] = commit_date_iso
    run_git(["add", "."], env=env)
    run_git(["commit", "--date", commit_date_iso, "-m", msg], env=env)

def last_commit_hash():
    out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
    return out.strip()

def main():
    subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, stdout=subprocess.DEVNULL)

    ensure_file_exists(TEXT_FILE)
    tz = datetime.now().astimezone().strftime("%z")

    today = date.today()
    d = START_DATE

    with open("commit_ids.txt", "a", encoding="utf-8") as log:
        while d <= today:
            n_commits = random.randint(0, 3)
            
            for _ in range(n_commits):
                commit_dt = datetime(d.year, d.month, d.day, random.randint(9, 23), random.randint(1, 50), random.randint(1, 50))
                commit_date_iso = commit_dt.strftime(f"%Y-%m-%d %H:%M:%S {tz}")

                append_random_char(TEXT_FILE)
                randmsg = random_string(50)  # generate 50-char commit message

                commit_with_date(commit_date_iso, randmsg)

                cid = last_commit_hash()
                log.write(f"{d.isoformat()} {cid} {randmsg}\n")
                log.flush()

                run_git(["push"])
                time.sleep(0.5)

            d += timedelta(days=1)

if __name__ == "__main__":
    main()
