"""Replays setup/readings.csv into SQLite at 1 row per second and runs the alert engine.

  python question_d/producer.py                  # real time: 1 row / s (2 hours)
  python question_d/producer.py --speed 20       # 20x faster, for development
  python question_d/producer.py --from-t 380     # start near the first anomaly
"""
import argparse, os, sqlite3, sys, time
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from alert_logic import AlertEngine
from common import CSV

DB = os.path.join(os.path.dirname(HERE), "wearables.db")


def connect(path=DB):
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def main(speed, from_t, db=DB):
    for ext in ("", "-wal", "-shm"):                 # fresh DB each run: no duplicates
        if os.path.exists(db + ext):
            os.remove(db + ext)
    conn = connect(db)
    conn.executescript("""
        CREATE TABLE readings(timestamp INTEGER PRIMARY KEY, hr REAL, acc REAL,
                              truth TEXT, ingested_at REAL);
        CREATE TABLE alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER,
                            kind TEXT, message TEXT, hr REAL, created_at REAL,
                            visible_at REAL);
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
    """)
    df = pd.read_csv(CSV)
    df = df[df.timestamp >= from_t].reset_index(drop=True)
    first_t, total = int(df.timestamp.iloc[0]), len(df)
    conn.executemany("INSERT INTO meta VALUES (?,?)",
                     [("total", str(total)), ("speed", str(speed)),
                      ("first_t", str(first_t)), ("status", "running")])
    conn.commit()

    eng, t0 = AlertEngine(), time.time()
    for i, r in enumerate(df.itertuples()):
        t = int(r.timestamp)
        now = time.time()
        conn.execute("INSERT INTO readings VALUES (?,?,?,?,?)", (t, r.hr, r.acc, r.anomaly_type, now))
        out = eng.step(t, r.hr, r.acc)               # the engine never sees 'truth'
        if out:
            kind, msg = out
            cur = conn.execute("INSERT INTO alerts(timestamp,kind,message,hr,created_at) VALUES (?,?,?,?,?)",
                               (t, kind, msg, r.hr, time.time()))
            print(f"ALERT {kind:12s} t={t:5d}s  {msg}", flush=True)
        conn.commit()
        if out:                                      # moment the alert became readable by the dashboard
            conn.execute("UPDATE alerts SET visible_at=? WHERE id=?", (time.time(), cur.lastrowid))
            conn.commit()
        wait = t0 + (i + 1) / speed - time.time()    # keeps a steady rhythm, no drift
        if wait > 0:
            time.sleep(wait)
    conn.execute("UPDATE meta SET value='finished' WHERE key='status'")
    conn.commit(); conn.close()
    print("stream finished", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=1.0, help="rows per second (1 = real time)")
    ap.add_argument("--from-t", type=int, default=0, help="start replay at this second")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()
    main(a.speed, a.from_t, a.db)
