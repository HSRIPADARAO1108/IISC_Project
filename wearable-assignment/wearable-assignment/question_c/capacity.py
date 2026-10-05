"""Question C, Level 3: capacity maths, step by step.  python question_c/capacity.py > capacity.md"""
USERS = 1000
def calc(users):
    rows_day = users * 86_400
    writes_s = users * 1
    rows_month = rows_day * 30
    payload = 20                       # user_id 4 + ts 8 + hr 4 + acc 4 bytes
    stored = 80                        # + tuple header, alignment, item pointer, PK index entry (assumed)
    return rows_day, writes_s, rows_month, rows_month * payload, rows_month * stored

print("# Capacity calculation (Question C, Level 3)\n")
print("Assumptions: 1 reading per user per second; row payload 20 B (user_id 4 + ts 8 + hr 4 + acc 4);\n"
      "about 80 B per row on disk once tuple header, alignment and the (user_id, ts) index are added (assumption).\n")
for u in (1_000, 100_000):
    d, w, m, raw, st = calc(u)
    print(f"## {u:,} users")
    print(f"1. Rows per day      = {u:,} users x 86,400 s = {d:,}")
    print(f"2. Writes per second = {u:,} users x 1 reading/s = {w:,} rows/s")
    print(f"3. Rows per month    = {d:,} x 30 = {m:,}")
    print(f"4. Raw payload/month = {m:,} x 20 B = {raw / 1e9:,.1f} GB")
    print(f"5. On-disk/month     = {m:,} x 80 B = {st / 1e9:,.0f} GB  (~{st / 1e12:.1f} TB)\n")
