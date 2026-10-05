import streamlit as st
import pandas as pd
import sqlite3

st.title("Wearable Patient Vital Monitoring & Live Anomaly Console")

conn = sqlite3.connect('wearables.db')
query = "SELECT * FROM readings ORDER BY timestamp DESC LIMIT 500"
df = pd.read_sql(query, conn)

if not df.empty:
    st.subheader("Live Heart Rate Stream")
    st.line_chart(df.set_index('timestamp')['hr'])
    
    st.subheader("Recent System Alerts")
    alerts_df = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20", conn)
    st.dataframe(alerts_df)
else:
    st.info("Waiting for data stream...")