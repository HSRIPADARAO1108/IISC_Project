"""Question C.  python question_c/system_design.py
Level 1: draws architecture.png.   Level 2: loads 3 users into SQLite, runs queries.sql.
Level 3: see capacity.py (rows/day, writes/s, storage/month) and capacity.md.
"""
import os, sqlite3, sys, datetime as dt
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "question_d"))
from common import load
from alert_logic import AlertEngine

OUT = os.path.join(HERE, "outputs"); os.makedirs(OUT, exist_ok=True)

# ---------------- Level 1: architecture picture ----------------
def draw_architecture():
    fig, ax = plt.subplots(figsize=(14, 6)); ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis("off")
    def box(x, y, w, h, text, c):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=c, ec="#333"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)
    def arrow(x1, y1, x2, y2, t=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", lw=1.4))
        if t: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, t, fontsize=7, ha="center")
    box(0.2, 2.4, 1.8, 1.2, "1,000 wearables\n1 reading/s each\n(hr, acc, user_id)", "#dbeafe")
    box(2.6, 2.4, 1.9, 1.2, "Ingestion gateway\nMQTT / HTTPS\nauth + validate", "#e0f2fe")
    box(5.1, 2.4, 1.8, 1.2, "Message queue\n(Kafka, partition\nby user_id)", "#fef9c3")
    box(7.6, 3.9, 2.2, 1.2, "Stream detector workers\n(AlertEngine state per user,\nspike / drop-out / drift)", "#dcfce7")
    box(7.6, 0.9, 2.2, 1.2, "Batch writer\n(COPY every 1-5 s)", "#dcfce7")
    box(10.4, 0.9, 1.9, 1.2, "Time-series DB\nreadings (partitioned)\nalerts, users", "#fae8ff")
    box(10.4, 3.9, 1.9, 1.2, "Alert service\npush / SMS / email\ndedupe 60 s", "#fee2e2")
    box(12.6, 2.4, 1.2, 1.2, "Dashboard\nAPI + web", "#ede9fe")
    arrow(2.0, 3.0, 2.6, 3.0); arrow(4.5, 3.0, 5.1, 3.0); arrow(6.9, 3.2, 7.6, 4.3); arrow(6.9, 2.8, 7.6, 1.6)
    arrow(9.8, 1.5, 10.4, 1.5); arrow(9.8, 4.5, 10.4, 4.5); arrow(11.35, 3.9, 11.35, 2.1, "alerts rows")
    arrow(12.3, 1.5, 13.0, 2.4); arrow(12.3, 4.5, 13.0, 3.6)
    ax.text(7, 5.7, "Architecture for 1,000 users (1 reading per second each)", ha="center", fontsize=12, weight="bold")
    plt.savefig(os.path.join(HERE, "architecture.png"), dpi=150, bbox_inches="tight"); plt.close(fig)


draw_architecture()

# ---------------- Level 2: load 3 users and run the SQL by hand ----------------
DBF = os.path.join(HERE, "wearables_system.db")
if os.path.exists(DBF):
    os.remove(DBF)                                               # re-runs never duplicate rows
conn = sqlite3.connect(DBF)
conn.executescript(open(os.path.join(HERE, "schema.sql")).read())

NOW = int(dt.datetime(2026, 10, 6, 12, 30, tzinfo=dt.timezone.utc).timestamp())   # reference "now"
# (user_id, name, recording starts this many seconds before NOW, HR offset in bpm)
USERS = [(1, "user_alpha", 2 * 3600, 0.0),        # recorded in the last 2 h
         (2, "user_beta", 30 * 3600, +6.0),       # older than 24 h
         (3, "user_gamma", 25 * 3600 + 900, -4.0)]  # straddles the 24 h boundary
base = load()
for uid, name, ago, hr_off in USERS:
    conn.execute("INSERT INTO users VALUES (?,?,?)", (uid, name, f"dev-{uid:04d}"))
    d = base.copy()
    start = NOW - ago
    d["ts"] = start + d["timestamp"]
    d["hr"] = d.hr.where(d.hr <= 0, d.hr + hr_off)                # shift real readings, keep 0 = sensor lost
    d.assign(user_id=uid)[["user_id", "ts", "hr", "acc"]].to_sql("readings", conn, if_exists="append", index=False)
    eng = AlertEngine()                                           # alerts come from the DETECTOR, not labels
    for r in d.itertuples():
        out = eng.step(int(r.timestamp), r.hr, r.acc)
        if out:
            conn.execute("INSERT INTO alerts(user_id,ts,kind,hr,message) VALUES (?,?,?,?,?)",
                         (uid, int(r.ts), out[0], r.hr, out[1]))
conn.commit()

sql = open(os.path.join(HERE, "queries.sql")).read()
queries = [q.strip() for q in sql.split(";") if "SELECT" in q]
titles = ["Q1  Alerts per user in the last 24 hours", "Q2  Users with more than 5 alerts in one hour",
          "Q3  Average heart rate per user per hour"]
lines = [f"reference NOW = {dt.datetime.fromtimestamp(NOW, dt.timezone.utc):%Y-%m-%d %H:%M} UTC",
         f"rows: readings={conn.execute('select count(*) from readings').fetchone()[0]}  "
         f"alerts={conn.execute('select count(*) from alerts').fetchone()[0]}  (per-user alerts below)"]
lines.append(pd.read_sql("SELECT user_id, kind, COUNT(*) n FROM alerts GROUP BY user_id, kind", conn)
             .pivot(index="user_id", columns="kind", values="n").fillna(0).astype(int).to_string())
for title, q in zip(titles, queries):
    res = pd.read_sql(q, conn, params={"now": NOW}) if ":now" in q else pd.read_sql(q, conn)
    lines.append(f"\n{title}\n{res.to_string(index=False)}")
text = "\n".join(lines)
print(text)
open(os.path.join(OUT, "query_outputs.txt"), "w").write(text)
conn.close()
