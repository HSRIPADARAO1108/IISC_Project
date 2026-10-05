"""Live wearable monitor (Question D, Level 1).

  terminal 1:  python question_d/producer.py --speed 5      (or use the Start button in the sidebar)
  terminal 2:  python -m streamlit run question_d/dashboard.py
"""
import os, sqlite3, subprocess, sys, time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), "wearables.db")
PRODUCER = os.path.join(HERE, "producer.py")

KIND = {"spike": ("#ff5a5f", "diamond", "Heart-rate spike"),
        "drop_out": ("#ffb020", "x", "Sensor drop-out"),
        "silent_drift": ("#b794f6", "triangle-up", "Silent drift")}
INK, MUTED, PANEL, LINE = "#e6edf3", "#8aa0b3", "#10202e", "#1d3347"
TRACE = "#4fd1c5"

st.set_page_config(page_title="Wearable monitor", page_icon="🫀", layout="wide")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap');
html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', system-ui, sans-serif; }}
.stApp {{ background: radial-gradient(1200px 600px at 10% -10%, #14304a 0%, #0a1620 55%) fixed; color:{INK}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.4rem; max-width: 1400px; }}
h1, h2, h3, p, label, span {{ color:{INK}; }}
.top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:.4rem; }}
.title {{ font-size:1.7rem; font-weight:600; letter-spacing:-.01em; }}
.sub {{ color:{MUTED}; font-size:.9rem; }}
.live {{ display:inline-flex; align-items:center; gap:.5rem; padding:.3rem .8rem; border-radius:999px;
        background:{PANEL}; border:1px solid {LINE}; font-size:.85rem; }}
.dot {{ width:10px; height:10px; border-radius:50%; background:#3ddc97; animation:pulse 1.2s infinite; }}
.dot.idle {{ background:#6b7c8c; animation:none; }}
@keyframes pulse {{ 0%{{box-shadow:0 0 0 0 rgba(61,220,151,.7)}} 70%{{box-shadow:0 0 0 10px rgba(61,220,151,0)}} 100%{{box-shadow:0 0 0 0 rgba(61,220,151,0)}} }}
.banner {{ border-radius:14px; padding:.9rem 1.2rem; margin:.6rem 0 1rem; font-size:1.05rem; border:1px solid {LINE}; }}
.banner.ok {{ background:linear-gradient(90deg,#0f3a35,#10202e); }}
.banner.walk {{ background:linear-gradient(90deg,#1b3a5b,#10202e); }}
.banner.alert {{ background:linear-gradient(90deg,#5c1a1f,#2a1218); border-color:#ff5a5f; animation:flash .9s infinite alternate; }}
@keyframes flash {{ from{{box-shadow:0 0 0 0 rgba(255,90,95,.0)}} to{{box-shadow:0 0 28px 2px rgba(255,90,95,.55)}} }}
.kpis {{ display:grid; grid-template-columns:repeat(5,1fr); gap:.8rem; margin-bottom:1rem; }}
.kpi {{ background:{PANEL}; border:1px solid {LINE}; border-radius:14px; padding:.9rem 1rem; }}
.kpi .l {{ color:{MUTED}; font-size:.8rem; }}
.kpi .v {{ font-family:'IBM Plex Mono',monospace; font-size:1.9rem; margin-top:.15rem; }}
.kpi .d {{ color:{MUTED}; font-size:.8rem; }}
.beat {{ display:inline-block; animation:beat 1s infinite; color:#ff5a5f; }}
@keyframes beat {{ 0%,100%{{transform:scale(1)}} 15%{{transform:scale(1.25)}} 30%{{transform:scale(1)}} 45%{{transform:scale(1.15)}} }}
.feed {{ display:flex; flex-direction:column; gap:.5rem; max-height:430px; overflow:auto; }}
.al {{ background:{PANEL}; border:1px solid {LINE}; border-left:5px solid var(--c); border-radius:10px; padding:.55rem .8rem; }}
.al.new {{ animation:slide .6s ease-out; }}
@keyframes slide {{ from{{transform:translateX(24px);opacity:0}} to{{transform:none;opacity:1}} }}
.al .k {{ font-weight:600; color:var(--c); }}
.al .m {{ color:{INK}; font-size:.88rem; }}
.al .t {{ color:{MUTED}; font-size:.78rem; font-family:'IBM Plex Mono',monospace; }}
@media (prefers-reduced-motion: reduce) {{ .dot,.beat,.banner.alert,.al.new {{ animation:none }} }}
@media (max-width:900px) {{ .kpis {{ grid-template-columns:repeat(2,1fr) }} }}
</style>""", unsafe_allow_html=True)

# ------------------------------ sidebar controls ------------------------------
st.sidebar.markdown("### Replay")
speed = st.sidebar.select_slider("Speed (rows per second)", [1, 2, 5, 10, 20, 60], value=5)
start_at = st.sidebar.number_input("Start at second", 0, 7000, 150, step=50)
if st.sidebar.button("Start live replay", width="stretch", type="primary"):
    subprocess.Popen([sys.executable, PRODUCER, "--speed", str(speed), "--from-t", str(int(start_at))],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    st.session_state.seen = set()
    time.sleep(1.0)
st.sidebar.markdown("### View")
window = st.sidebar.slider("Seconds shown", 60, 1800, 420, step=30)
show_truth = st.sidebar.toggle("Overlay ground truth", value=False,
                               help="Draws the labelled anomalies behind the signal so you can check the detector.")
refresh = st.sidebar.select_slider("Refresh every (s)", [0.5, 1, 2, 3], value=1)
st.sidebar.caption("The alert engine in question_d/alert_logic.py sees one reading at a time and never the labels.")


def q(sql, conn):
    try:
        return pd.read_sql(sql, conn)
    except Exception:
        return pd.DataFrame()


def spans(mask, ts):
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return []
    return [(ts[g[0]], ts[g[-1]]) for g in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)]


@st.fragment(run_every=refresh)
def live():
    if not os.path.exists(DB):
        st.markdown(f'<div class="banner ok">No data yet. Press <b>Start live replay</b> in the sidebar, '
                    f'or run <code>python question_d/producer.py</code>.</div>', unsafe_allow_html=True)
        return
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    rd = q(f"SELECT * FROM readings ORDER BY timestamp DESC LIMIT {int(window)}", conn).sort_values("timestamp")
    al = q("SELECT * FROM alerts ORDER BY id DESC", conn)
    meta = q("SELECT * FROM meta", conn)
    cnt_df = q("SELECT COUNT(*) n FROM readings", conn)
    conn.close()
    if rd.empty:
        st.info("Waiting for the first reading...")
        return
    meta = dict(zip(meta.key, meta.value)) if not meta.empty else {}
    total, status = int(meta.get("total", 0) or 0), meta.get("status", "running")
    last = rd.iloc[-1]
    t_now, hr_now, acc_now = int(last.timestamp), float(last.hr), float(last.acc)
    n_done = int(cnt_df.n[0]) if not cnt_df.empty else len(rd)
    moving = acc_now >= 0.3

    # --- header
    live_cls = "dot" if status == "running" else "dot idle"
    st.markdown(f'<div class="top"><div><div class="title">Wearable heart monitor</div>'
                f'<div class="sub">Seed 2518 recording, replayed as a live stream</div></div>'
                f'<div class="live"><span class="{live_cls}"></span>{"Live" if status=="running" else "Finished"} '
                f'&nbsp;|&nbsp; second {t_now:,}</div></div>', unsafe_allow_html=True)

    # --- status banner (pulses red for ~10 stream seconds after an alert)
    recent = al[al.timestamp >= t_now - 10] if not al.empty else al
    if not recent.empty:
        a0 = recent.iloc[0]
        st.markdown(f'<div class="banner alert"><b>{KIND[a0.kind][2]}</b>: {a0.message}</div>', unsafe_allow_html=True)
    elif hr_now <= 0:
        st.markdown('<div class="banner alert"><b>No signal</b>: the sensor is reporting zero.</div>', unsafe_allow_html=True)
    elif moving:
        st.markdown('<div class="banner walk">You are moving. A higher heart rate is expected and is not flagged.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner ok">Everything looks normal. Heart rate is steady while resting.</div>', unsafe_allow_html=True)

    # --- KPI cards
    prev = float(rd.hr.iloc[-6]) if len(rd) > 6 else hr_now
    delta = hr_now - prev
    last_al = f"{KIND[al.iloc[0].kind][2]}" if not al.empty else "none yet"
    since = f"{t_now - int(al.iloc[0].timestamp)} s ago" if not al.empty else "-"
    pct = (n_done / total * 100) if total else 0
    st.markdown(f"""<div class="kpis">
      <div class="kpi"><div class="l">Heart rate</div><div class="v"><span class="beat">&#10084;</span> {hr_now:.0f}</div><div class="d">bpm, {delta:+.0f} over 5 s</div></div>
      <div class="kpi"><div class="l">Activity</div><div class="v">{"Walking" if moving else "Resting"}</div><div class="d">movement {acc_now:.2f}</div></div>
      <div class="kpi"><div class="l">Alerts raised</div><div class="v">{len(al)}</div><div class="d">spike {int((al.kind=='spike').sum()) if not al.empty else 0} | drop-out {int((al.kind=='drop_out').sum()) if not al.empty else 0} | drift {int((al.kind=='silent_drift').sum()) if not al.empty else 0}</div></div>
      <div class="kpi"><div class="l">Last alert</div><div class="v" style="font-size:1.15rem;padding-top:.5rem">{last_al}</div><div class="d">{since}</div></div>
      <div class="kpi"><div class="l">Replay progress</div><div class="v">{pct:.0f}%</div><div class="d">{n_done:,} of {total:,} readings</div></div></div>""",
                unsafe_allow_html=True)

    # --- main signal chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.04)
    ts = rd.timestamp.to_numpy()
    for a, b in spans(rd.acc.to_numpy() >= 0.3, ts):                         # walking = calm blue band
        fig.add_vrect(x0=a, x1=b, fillcolor="#3b82f6", opacity=0.12, line_width=0, row="all", col=1)
    if show_truth:                                                           # ground truth = outlined bands
        for k, (c, _, nm) in KIND.items():
            for a, b in spans((rd.truth == k).to_numpy(), ts):
                fig.add_vrect(x0=a, x1=b + 1, fillcolor=c, opacity=0.18, line=dict(color=c, width=1, dash="dot"),
                              row=1, col=1)
    hr_plot = rd.hr.where(rd.hr > 0)                                         # gap, not a dive to zero
    fig.add_trace(go.Scatter(x=ts, y=hr_plot, mode="lines", line=dict(color=TRACE, width=2.2),
                             fill="tozeroy", fillcolor="rgba(79,209,197,0.07)", name="Heart rate",
                             hovertemplate="%{x}s: %{y:.0f} bpm<extra></extra>"), row=1, col=1)
    zeros = rd[rd.hr <= 0]
    if not zeros.empty:
        fig.add_trace(go.Scatter(x=zeros.timestamp, y=[rd.hr[rd.hr > 0].min() - 5 if (rd.hr > 0).any() else 0] * len(zeros),
                                 mode="markers", marker=dict(color="#ffb020", symbol="x", size=7),
                                 name="Sensor reads 0", hoverinfo="skip"), row=1, col=1)
    vis = al[al.timestamp >= ts.min()] if not al.empty else al
    for k, (c, sym, nm) in KIND.items():
        g = vis[vis.kind == k] if not vis.empty else vis
        if len(g):
            y = [float(rd.loc[rd.timestamp == t_, "hr"].iloc[0]) if (rd.timestamp == t_).any() else np.nan for t_ in g.timestamp]
            y = [v if v > 0 else (rd.hr[rd.hr > 0].min() - 5 if (rd.hr > 0).any() else 0) for v in y]
            fig.add_trace(go.Scatter(x=g.timestamp, y=y, mode="markers", name=nm,
                                     marker=dict(color=c, symbol=sym, size=15, line=dict(color="white", width=1.5)),
                                     text=g.message, hovertemplate="%{text}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=ts, y=rd.acc, mode="lines", line=dict(color="#7aa2f7", width=1.5),
                             fill="tozeroy", fillcolor="rgba(122,162,247,0.18)", name="Movement",
                             hovertemplate="%{x}s: %{y:.2f}<extra></extra>"), row=2, col=1)
    fig.add_hline(y=0.3, line=dict(color=MUTED, width=1, dash="dot"), row=2, col=1)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(16,32,46,0.85)", font=dict(color=INK, family="IBM Plex Sans"),
                      legend=dict(orientation="h", y=1.06, x=0), hovermode="x unified", uirevision="keep")
    fig.update_xaxes(gridcolor=LINE, zeroline=False); fig.update_yaxes(gridcolor=LINE, zeroline=False)
    fig.update_yaxes(title_text="bpm", row=1, col=1); fig.update_yaxes(title_text="movement", row=2, col=1)
    fig.update_xaxes(title_text="second of recording", row=2, col=1)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # --- lower row: gauge | alert mix | feed
    c1, c2, c3 = st.columns([1, 1, 1.35])
    with c1:
        g = go.Figure(go.Indicator(mode="gauge+number", value=max(hr_now, 0), number=dict(suffix=" bpm", font=dict(color=INK)),
                                   gauge=dict(axis=dict(range=[0, 180], tickcolor=MUTED), bar=dict(color=TRACE if hr_now > 0 else "#ffb020"),
                                              bgcolor=PANEL, borderwidth=0,
                                              steps=[dict(range=[0, 40], color="#3a2a14"), dict(range=[40, 100], color="#123a36"),
                                                     dict(range=[100, 130], color="#3a3314"), dict(range=[130, 180], color="#4a1a1f")])))
        g.update_layout(height=270, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)",
                        title=dict(text="Heart rate now", font=dict(size=14, color=MUTED)))
        st.plotly_chart(g, width="stretch", config={"displayModeBar": False})
    with c2:
        if al.empty:
            st.markdown(f'<div class="kpi" style="height:240px"><div class="l">Alert mix</div><div class="d" style="margin-top:2rem">Waiting for the first alert.</div></div>', unsafe_allow_html=True)
        else:
            cnt = al.kind.value_counts()
            d = go.Figure(go.Pie(labels=[KIND[k][2] for k in cnt.index], values=cnt.values, hole=0.62,
                                 marker=dict(colors=[KIND[k][0] for k in cnt.index], line=dict(color="#0a1620", width=3)),
                                 textinfo="value", sort=False))
            d.update_layout(height=270, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color=INK), showlegend=True, legend=dict(orientation="h", y=-0.05),
                            title=dict(text="Alert mix", font=dict(size=14, color=MUTED)))
            st.plotly_chart(d, width="stretch", config={"displayModeBar": False})
    with c3:
        st.markdown(f"<div class='sub' style='margin-bottom:.4rem'>Alert feed (newest first)</div>", unsafe_allow_html=True)
        if al.empty:
            st.markdown('<div class="al" style="--c:#6b7c8c"><span class="m">No alerts so far.</span></div>', unsafe_allow_html=True)
        else:
            seen = st.session_state.setdefault("seen", set())
            html = ""
            for r in al.head(12).itertuples():
                cls = "al new" if r.id not in seen else "al"
                html += (f'<div class="{cls}" style="--c:{KIND[r.kind][0]}"><div class="k">{KIND[r.kind][2]}'
                         f'<span class="t"> &nbsp; t={r.timestamp}s</span></div><div class="m">{r.message}</div></div>')
            seen.update(al.id.tolist())
            st.markdown(f'<div class="feed">{html}</div>', unsafe_allow_html=True)

    # --- evaluation (only meaningful because we also kept the labels in the DB)
    with st.expander("How fast were the alerts? (spike and drop-out start to alert)"):
        rows = []
        truth = rd[rd.truth.isin(["spike", "drop_out"])]
        for k in ("spike", "drop_out"):
            tk = truth[truth.truth == k].timestamp.to_numpy()
            for a_, b_ in spans(np.isin(rd.timestamp.to_numpy(), tk), rd.timestamp.to_numpy()):
                hit = al[(al.kind == k) & (al.timestamp >= a_) & (al.timestamp <= b_)] if not al.empty else al
                if len(hit):
                    rows.append({"type": KIND[k][2], "starts at (s)": a_, "alert at (s)": int(hit.timestamp.min()),
                                 "delay (s)": int(hit.timestamp.min() - a_)})
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True) if rows else st.caption("No finished events in view yet.")


live()
