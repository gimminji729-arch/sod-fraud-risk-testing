"""
Synthetic data generator for:
  Transaction-Level SoD & Fraud Risk Testing - Haneul Freight & Logistics (fictional)

All company, employee, customer and carrier names are fictional.
No real company data is used. Output: haneul_logistics_audit.db (SQLite)
Audit period: 2026-01-02 to 2026-03-31
"""
import sqlite3, random, math, os
from datetime import datetime, date, timedelta, time

random.seed(20260331)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haneul_logistics_audit.db")

PERIOD_START = date(2026, 1, 2)
PERIOD_END = datetime(2026, 3, 31, 23, 59, 59)
HOLIDAYS = {date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 3, 2)}
FMT = "%Y-%m-%d %H:%M:%S"

def is_workday(d):
    return d.weekday() < 5 and d not in HOLIDAYS

def add_workdays(d, n):
    while n > 0:
        d += timedelta(days=1)
        if is_workday(d):
            n -= 1
    return d

WORKDAYS = []
_d = PERIOD_START
while _d <= PERIOD_END.date():
    if is_workday(_d):
        WORKDAYS.append(_d)
    _d += timedelta(days=1)

def ts(d, start_h=8.6, end_h=18.4):
    m = random.randint(int(start_h * 60), int(end_h * 60))
    return datetime.combine(d, time(m // 60, m % 60, random.randint(0, 59)))

def s(dt):
    return dt.strftime(FMT) if dt else None

# ---------------------------------------------------------------- employees
EMP = [
    ("E001", "Kang Doyun", "Operations", "Operations Manager", "OPS_MANAGER", "2019-03-04"),
    ("E002", "Yoon Seoyeon", "Finance", "Finance Manager", "FINANCE", "2018-07-02"),
    ("E003", "Lim Hajun", "Customer Service", "CS Associate", "CS_AGENT", "2023-02-13"),
    ("E004", "Choi Yerin", "Customer Service", "CS Associate", "CS_AGENT", "2022-09-05"),
    ("E005", "Jung Minho", "Customer Service", "CS Associate", "CS_AGENT", "2024-04-01"),
    ("E006", "Han Sua", "Customer Service", "CS Lead", "CS_AGENT", "2021-01-11"),
    ("E007", "Seo Jaehyun", "Operations", "Operations Coordinator", "OPS_COORDINATOR", "2020-06-15"),
    ("E008", "Oh Nayeon", "Operations", "Operations Coordinator", "OPS_COORDINATOR", "2023-08-21"),
    ("E009", "Bae Sungho", "Warehouse", "Warehouse Lead", "WAREHOUSE_LEAD", "2017-05-08"),
    ("E010", "Moon Jiho", "Warehouse", "Warehouse Associate", "WAREHOUSE_STAFF", "2024-01-08"),
    ("E011", "Song Eunwoo", "Warehouse", "Warehouse Associate", "WAREHOUSE_STAFF", "2022-11-21"),
    ("E012", "Ahn Haeun", "Warehouse", "Warehouse Associate", "WAREHOUSE_STAFF", "2025-03-17"),
    ("E013", "Jo Seungmin", "Warehouse", "Warehouse Associate", "WAREHOUSE_STAFF", "2023-06-05"),
    ("E014", "Hwang Dongha", "Transportation", "Dispatch Coordinator", "DISPATCH", "2020-02-03"),
    ("E015", "Yang Soyeon", "Transportation", "Dispatch Coordinator", "DISPATCH", "2022-05-16"),
    ("E016", "Nam Kyungsoo", "Transportation", "Dispatch Coordinator", "DISPATCH", "2024-08-26"),
    ("E017", "Shin Taeho", "IT", "IT Administrator", "IT_ADMIN", "2021-10-18"),
    ("E018", "Kwon Jiae", "Finance", "Accounts Payable Specialist", "FINANCE", "2022-03-14"),
]
CS = ["E003", "E004", "E005", "E006"]
WH_STAFF = ["E010", "E011", "E012", "E013"]
DISPATCH = ["E014", "E015", "E016"]

# ---------------------------------------------------------------- customers
cities = ["Incheon", "Pyeongtaek", "Gimpo", "Ansan", "Hwaseong", "Cheonan", "Busan",
          "Daegu", "Gwangju", "Ulsan", "Siheung", "Asan", "Gunpo", "Yongin", "Changwon"]
kinds = ["Trading", "Electronics", "Auto Parts", "Foods", "Textiles", "Medical Supply",
         "Cosmetics", "Home Goods", "Industrial", "Pet Supply"]
customers = []
used = set()
for i in range(1, 31):
    while True:
        nm = f"{random.choice(cities)} {random.choice(kinds)} Co."
        if nm not in used:
            used.add(nm); break
    onboard = date(2021, 1, 1) + timedelta(days=random.randint(0, 1400))
    customers.append([f"CUST-{i:03d}", nm, s(ts(onboard)), "E006"])
# red-flag customer: onboarded right before the period by the coordinator
customers[23][2] = "2025-12-29 19:47:12"
customers[23][3] = "E007"
CUST_IDS = [c[0] for c in customers]
FLAG_CUST = ["CUST-011", "CUST-024"]

# ---------------------------------------------------------------- skus
cats = [("Consumer Electronics", 150_000, 1_600_000), ("Auto Parts", 40_000, 900_000),
        ("Cosmetics", 8_000, 90_000), ("Medical Devices", 200_000, 2_400_000),
        ("Home Goods", 10_000, 180_000), ("Industrial Tools", 60_000, 1_200_000)]
skus = []
for i in range(1, 61):
    cat, lo, hi = random.choice(cats)
    cost = int(round(math.exp(random.uniform(math.log(lo), math.log(hi))), -2))
    skus.append((f"SKU-{i:04d}", f"{cat} item {i:02d}", cat, cost))
HIGH_SKUS = [k for k in skus if k[3] >= 600_000]

CARRIERS = ["Saebit Express", "Hangang Linehaul", "Dasom Parcel"]

# ---------------------------------------------------------------- shipments
shipments = []          # dicts
for d in WORKDAYS:
    for _ in range(random.randint(42, 56)):
        r = random.random()
        creator = random.choice(CS) if r < 0.70 else ("E007" if r < 0.85 else "E008")
        val = int(round(min(max(random.lognormvariate(math.log(650_000), 0.75), 50_000), 7_500_000), -3))
        shipments.append(dict(customer=random.choice(CUST_IDS), created_by=creator,
                              created_at=ts(d), carrier=random.choice(CARRIERS), value=val,
                              plan="NORMAL"))
shipments.sort(key=lambda x: x["created_at"])
for i, sh in enumerate(shipments, 1):
    sh["id"] = f"SHP-{260000 + i}"

def pick(cond, n):
    pool = [sh for sh in shipments if sh["plan"] == "NORMAL" and cond(sh)]
    chosen = random.sample(pool, n)
    return chosen

# ---- planted scenarios (assign plans before natural exceptions) -------------
def between(a, b):
    return lambda sh: a <= sh["created_at"].date() <= b

f1 = pick(between(date(2026, 1, 6), date(2026, 2, 6)), 7)
for i, sh in enumerate(f1):
    sh["plan"] = "F1_POD" if i < 2 else "F1"
    sh["customer"] = FLAG_CUST[i % 2] if i < 5 else sh["customer"]
    sh["value"] = random.randrange(520_000, 590_000, 1000)
    sh["created_by"] = "E007" if i % 3 == 0 else sh["created_by"]

f2 = pick(between(date(2026, 2, 19), date(2026, 3, 11)), 5)
f2_amounts = [921_400, 1_184_300, 1_462_800, 1_873_500, 1_944_200]
for i, sh in enumerate(f2):
    sh["plan"] = "F2_POD" if i == 0 else "F2"
    sh["customer"] = FLAG_CUST[i % 2] if i < 4 else sh["customer"]
    sh["value"] = int(round(f2_amounts[i] / random.uniform(0.9, 0.97), -3))
    sh["claim_amt"] = f2_amounts[i]

bulk = pick(between(date(2026, 3, 24), date(2026, 3, 27)), 28)
for sh in bulk:
    sh["plan"] = "BULK"

# natural exceptions only for shipments created up to 2026-03-20
for sh in shipments:
    if sh["plan"] != "NORMAL" or sh["created_at"].date() > date(2026, 3, 20):
        continue
    r = random.random()
    if r < 0.024:   sh["plan"] = "X_DELAY"
    elif r < 0.044: sh["plan"] = "X_DAMAGED"
    elif r < 0.056: sh["plan"] = "X_LOST"
    elif r < 0.066: sh["plan"] = "X_ADDRESS"
    elif r < 0.072: sh["plan"] = "X_REFUSED"

# ---------------------------------------------------------------- build events
status_log, pods, exceptions, claims = [], [], [], []

def log(sh, status, by, at):
    status_log.append([sh["id"], status, by, at])

def after_hours(d):
    h = random.choice([21, 21, 22, 22, 23])
    return datetime.combine(d, time(h, random.randint(0, 59), random.randint(0, 59)))

self_close_budget = 6   # natural low-risk self-closures by CS
noise_near = []         # natural near-threshold claims (E008)

for sh in shipments:
    c = sh["created_at"]
    log(sh, "CREATED", sh["created_by"], c)
    picked = ts(c.date(), max(c.hour + c.minute / 60 + 0.5, 8.6), 18.6) if c.hour < 17 else ts(add_workdays(c.date(), 1))
    log(sh, "PICKED", random.choice(WH_STAFF), picked)
    transit = ts(add_workdays(picked.date(), 1), 8.6, 12.0)
    log(sh, "IN_TRANSIT", random.choice(DISPATCH), transit)
    deliver_day = add_workdays(transit.date(), random.choice([1, 1, 2, 2, 3]))
    delivered = ts(deliver_day, 9.0, 20.5)
    plan = sh["plan"]
    sh["disp"] = random.choice(DISPATCH)

    if plan in ("NORMAL", "X_DELAY", "X_ADDRESS", "X_DAMAGED", "F1_POD", "F2_POD"):
        if plan == "X_DELAY":
            deliver_day = add_workdays(deliver_day, random.randint(2, 4))
            delivered = ts(deliver_day, 9.0, 20.5)
        if delivered <= PERIOD_END:
            log(sh, "DELIVERED", sh["disp"], delivered)
            pods.append([sh["id"], s(delivered - timedelta(minutes=random.randint(1, 9))),
                         "Consignee on site", sh["disp"]])
        sh["delivered"] = delivered

    if plan == "X_DAMAGED":
        dmg = delivered + timedelta(minutes=random.randint(8, 40))
        if dmg.hour >= 19 or dmg.hour < 8:
            dmg = ts(add_workdays(delivered.date(), 1), 8.8, 10.5)
        log(sh, "DAMAGED", sh["disp"], dmg)
        sh["event"] = dmg
    elif plan == "X_LOST":
        lost = ts(add_workdays(transit.date(), random.randint(3, 6)))
        log(sh, "LOST", sh["disp"], lost)
        sh["event"] = lost
    elif plan == "X_REFUSED":
        ret = ts(add_workdays(transit.date(), random.randint(2, 3)))
        log(sh, "RETURNED", sh["disp"], ret)
        sh["event"] = ret
    elif plan in ("X_DELAY", "X_ADDRESS"):
        sh["event"] = ts(add_workdays(transit.date(), 1))
    elif plan in ("F1", "F1_POD", "F2", "F2_POD"):
        idx = (f1 + f2).index(sh)
        base = add_workdays(sh["delivered"].date(), random.randint(1, 3)) if plan.endswith("POD") \
            else add_workdays(transit.date(), random.randint(2, 4))
        late = idx in (1, 3, 5, 8, 10)
        lost = after_hours(base) if late else ts(base, 13.0, 18.3)
        log(sh, "LOST", "E007", lost)
        sh["event"] = lost
    elif plan == "BULK":
        pass

# bulk quarter-end DELIVERED updates without POD by E008
t0 = datetime(2026, 3, 31, 18, 52, 3)
for i, sh in enumerate(bulk):
    log(sh, "DELIVERED", "E008", t0 + timedelta(seconds=int(i * 15.5 + random.randint(0, 6))))

# drop anything after the period
status_log = [r for r in status_log if r[3] <= PERIOD_END]
pods = [p for p in pods if p[1] <= s(PERIOD_END)]

# ---------------------------------------------------------------- exceptions & claims
EXC_TYPE = {"X_DELAY": "DELAY", "X_DAMAGED": "DAMAGED", "X_LOST": "LOST",
            "X_ADDRESS": "ADDRESS_CORRECTION", "X_REFUSED": "REFUSED"}

def natural_approver(amount):
    if amount > 500_000:
        return "E001"
    return random.choices(["E007", "E008", "E001"], weights=[35, 35, 30])[0]

near_noise_left = [468_900, 491_300]
for sh in shipments:
    plan = sh["plan"]
    if plan in EXC_TYPE:
        etype = EXC_TYPE[plan]
        ev = sh["event"]
        reg_at = ev + timedelta(minutes=random.randint(15, 180))
        if reg_at.hour >= 19:
            reg_at = ts(add_workdays(ev.date(), 1), 8.7, 11)
        if etype in ("DAMAGED", "LOST"):
            reg_by = random.choices(["E007", "E008", "E006"], weights=[3, 3, 4])[0]
        else:
            reg_by = random.choice(CS)
        if etype in ("DELAY", "ADDRESS_CORRECTION") and self_close_budget > 0 and random.random() < 0.35:
            self_close_budget -= 1
            close_by, close_at = reg_by, reg_at + timedelta(minutes=random.randint(20, 150))
            if close_at.hour >= 19:
                close_at = reg_at + timedelta(minutes=random.randint(8, 25))
        else:
            if etype in ("DAMAGED", "LOST"):
                close_by = random.choice([p for p in ["E001", "E001", "E008", "E007"] if p != reg_by])
            else:
                close_by = random.choice([p for p in ["E006", "E007", "E008"] if p != reg_by])
            close_at = ts(add_workdays(reg_at.date(), random.randint(1, 6)))
        res = {"DELAY": "Customer notified; delivered late", "DAMAGED": "Claim processed",
               "LOST": "Claim processed", "ADDRESS_CORRECTION": "Address updated and re-routed",
               "REFUSED": "Returned to shipper"}[etype]
        exc = dict(ship=sh["id"], type=etype, reg_by=reg_by, reg_at=reg_at,
                   close_by=close_by, close_at=close_at, res=res, cust=sh["customer"])
        exceptions.append(exc)

        if etype in ("DAMAGED", "LOST") and random.random() < 0.9:
            frac = random.uniform(0.85, 1.0) if etype == "LOST" else random.uniform(0.1, 0.5)
            amt = int(round(sh["value"] * frac, -2))
            if 450_000 <= amt <= 500_000:
                amt = int(round(amt * 0.82, -2))
            if 1_800_000 <= amt <= 2_000_000:
                amt = int(round(amt * 1.12, -2))
            sub_at = ts(add_workdays(reg_at.date(), random.randint(0, 2)))
            appr = natural_approver(amt)
            if near_noise_left and amt <= 500_000 and sub_at.date() < date(2026, 2, 14) and random.random() < 0.15:
                amt = near_noise_left.pop(); appr = "E008"
            rejected = appr == "E001" and random.random() < 0.08
            appr_at = ts(add_workdays(sub_at.date(), random.randint(0, 3)))
            claims.append(dict(ship=sh["id"], exc=exc, cust=sh["customer"], type=etype, amt=amt,
                               sub_by=random.choice(CS), sub_at=sub_at, appr=appr, appr_at=appr_at,
                               status="REJECTED" if rejected else "APPROVED",
                               reason="Insufficient supporting documents" if rejected else None))

# planted: F1 / F2 exceptions and claims (E007)
def office(dt, base_day):
    """push late-night / early-morning activity to the next workday morning"""
    if 8 <= dt.hour < 19 and is_workday(dt.date()):
        return dt
    return ts(add_workdays(base_day, 1), 8.7, 9.8)

for i, sh in enumerate(f1 + f2):
    ev = sh["event"]
    reg_at = ev + timedelta(minutes=random.randint(6, 35))
    sub_at = office(reg_at + timedelta(minutes=random.randint(20, 90)), ev.date())
    appr_at = office(sub_at + timedelta(hours=random.uniform(0.4, 2.5)), sub_at.date())
    close_self = not (i == 11)
    close_by = "E007" if close_self else "E008"
    if close_self:
        close_at = min(appr_at + timedelta(minutes=random.randint(10, 80)),
                       reg_at + timedelta(hours=23, minutes=random.randint(0, 40)))
    else:
        close_at = ts(add_workdays(reg_at.date(), 2))
    exc = dict(ship=sh["id"], type="LOST", reg_by="E007", reg_at=reg_at, close_by=close_by,
               close_at=close_at, res="Claim processed", cust=sh["customer"])
    exceptions.append(exc)
    if sh["plan"].startswith("F1"):
        amt = random.randrange(455_000, 499_000, 100)
    else:
        amt = sh["claim_amt"]
    sub_by = "E007" if (i % 2 == 0 or sh["plan"].startswith("F2")) else "E005"
    claims.append(dict(ship=sh["id"], exc=exc, cust=sh["customer"], type="LOST", amt=amt,
                       sub_by=sub_by, sub_at=sub_at, appr="E007", appr_at=appr_at,
                       status="APPROVED", reason=None))

# planted: duplicate claims by E007 on two F1 shipments (resubmitted weeks later)
for sh, gap in ((f1[1], 26), (f1[4], 31)):
    orig = next(c for c in claims if c["ship"] == sh["id"])
    sub_at = ts(orig["sub_at"].date() + timedelta(days=gap), 14.0, 18.0)
    while not is_workday(sub_at.date()):
        sub_at += timedelta(days=1)
    claims.append(dict(ship=sh["id"], exc=orig["exc"], cust=orig["cust"], type="LOST",
                       amt=orig["amt"] + random.choice([-3_600, 2_900]), sub_by="E007",
                       sub_at=sub_at, appr="E007", appr_at=sub_at + timedelta(minutes=47),
                       status="APPROVED", reason=None))

# noise: CS double-entry caught by manager (control worked)
dmg = [c for c in claims if c["type"] == "DAMAGED" and c["status"] == "APPROVED"
       and c["appr"] == "E001" and c["sub_by"] == "E004"]
if not dmg:
    dmg = [c for c in claims if c["type"] == "DAMAGED" and c["status"] == "APPROVED" and c["appr"] == "E001"]
o = dmg[0]
o["sub_by"] = "E004"
claims.append(dict(ship=o["ship"], exc=o["exc"], cust=o["cust"], type="DAMAGED", amt=o["amt"],
                   sub_by="E004", sub_at=o["sub_at"] + timedelta(days=1, minutes=12), appr="E001",
                   appr_at=o["sub_at"] + timedelta(days=2, hours=1), status="REJECTED",
                   reason="Duplicate submission"))

# noise: E008 approves a >500k claim during the unauthorized window
cand = [c for c in claims if c["type"] == "DAMAGED" and c["appr"] == "E001"
        and date(2026, 3, 3) <= c["appr_at"].date() <= date(2026, 3, 13)]
if cand:
    n3 = cand[0]
else:
    n3 = [c for c in claims if c["type"] == "DAMAGED" and c["appr"] == "E001"][-1]
    n3["appr_at"] = datetime(2026, 3, 5, 15, 22, 41)
n3["amt"], n3["appr"], n3["status"], n3["reason"] = 680_000, "E008", "APPROVED", None

# noise: E008 records a DAMAGED status and approves the related claim (SoD, low value)
n1 = next(c for c in claims if c["type"] == "DAMAGED" and c["appr"] in ("E008", "E007", "E001")
          and c["amt"] < 200_000 and c is not n3 and c is not o)
for r in status_log:
    if r[0] == n1["ship"] and r[1] == "DAMAGED":
        r[2] = "E008"
n1["appr"], n1["status"], n1["reason"] = "E008", "APPROVED", None

# keep declared value consistent with claim amounts
ship_by_id = {x["id"]: x for x in shipments}
for c in claims:
    sh = ship_by_id[c["ship"]]
    cap = 0.95 if c["type"] == "LOST" else 0.5
    if c["amt"] > sh["value"] * cap:
        sh["value"] = int(round(c["amt"] / (cap * random.uniform(0.9, 0.98)), -3))

# guarantee: no natural claim approved after period end
claims = [c for c in claims if c["appr_at"] <= PERIOD_END and c["sub_at"] <= PERIOD_END]
exceptions = [e for e in exceptions if e["reg_at"] <= PERIOD_END]
for e in exceptions:
    if e["close_at"] > PERIOD_END:
        e["close_by"], e["close_at"], e["res"] = None, None, None

# ids
exceptions.sort(key=lambda e: e["reg_at"])
for i, e in enumerate(exceptions, 1):
    e["id"] = f"EXC-{i:04d}"
claims.sort(key=lambda c: c["sub_at"])
for i, c in enumerate(claims, 1):
    c["id"] = f"CLM-{i:04d}"
    if c["status"] == "APPROVED":
        pd = add_workdays(c["appr_at"].date(), random.randint(2, 5))
        c["paid_amount"], c["paid_date"] = c["amt"], pd.isoformat()
        if pd > PERIOD_END.date():
            c["paid_amount"], c["paid_date"] = None, None
    else:
        c["paid_amount"], c["paid_date"] = 0, None

# ---------------------------------------------------------------- inventory adjustments
adjs = []
REASONS = ["CYCLE_COUNT_VARIANCE", "DAMAGED_IN_WAREHOUSE", "RECEIVING_ERROR", "RETURN_RESTOCK"]
for d in WORKDAYS:
    for _ in range(random.choice([2, 3, 3, 4, 4, 5])):
        sku = random.choice(skus)
        by = random.choice(WH_STAFF + ["E009"])
        reason = random.choice(REASONS)
        qty = random.randint(1, 6) * (1 if reason == "RETURN_RESTOCK" else random.choice([-1, -1, -1, 1]))
        if abs(qty) * sku[3] >= 1_000_000 and random.random() < 0.6:
            qty = int(math.copysign(1, qty))
        value = abs(qty) * sku[3]
        appr = "E001" if (by == "E009" or value >= 1_000_000) else "E009"
        at = ts(d)
        adjs.append(dict(sku=sku[0], qty=qty, reason=reason, by=by, at=at, appr=appr,
                         appr_at=at + timedelta(hours=random.uniform(0.5, 6))))

planted_adj = []
days_q = [d for d in WORKDAYS if d.month in (1, 2, 3)]
for k in range(5):   # E009, no approval
    sku = random.choice(HIGH_SKUS); d = random.choice(days_q)
    planted_adj.append(dict(sku=sku[0], qty=-random.randint(2, 4), reason=random.choice(["DAMAGED_IN_WAREHOUSE", "CYCLE_COUNT_VARIANCE"]),
                            by="E009", at=ts(d, 17.0, 18.6), appr=None, appr_at=None))
for k in range(3):   # E009 self-approved
    sku = random.choice(HIGH_SKUS); d = random.choice(days_q); at = ts(d, 16.5, 18.4)
    planted_adj.append(dict(sku=sku[0], qty=-random.randint(2, 3), reason="DAMAGED_IN_WAREHOUSE",
                            by="E009", at=at, appr="E009", appr_at=at + timedelta(minutes=random.randint(2, 9))))
for k in range(3):   # staff >= 1M approved by lead instead of manager
    sku = random.choice(HIGH_SKUS); d = random.choice(days_q); at = ts(d)
    qty = -max(2, math.ceil(1_050_000 / sku[3]))
    planted_adj.append(dict(sku=sku[0], qty=qty, reason="CYCLE_COUNT_VARIANCE",
                            by="E011", at=at, appr="E009", appr_at=at + timedelta(hours=1, minutes=13)))
adjs += planted_adj
adjs.sort(key=lambda a: a["at"])
for i, a in enumerate(adjs, 1):
    a["id"] = f"ADJ-{i:04d}"

# ---------------------------------------------------------------- config history
config = [
    ("CFG-001", "CLAIM_APPROVAL_LIMIT_NON_MANAGER", 500000, "2025-01-01 00:00:00", "2026-02-16 22:41:07", "E017", "CHG-2024-118", "E001"),
    ("CFG-002", "INV_ADJ_MANAGER_APPROVAL_THRESHOLD", 1000000, "2025-01-01 00:00:00", None, "E017", "CHG-2024-119", "E001"),
    ("CFG-003", "EXCEPTION_AUTO_ESCALATION_DAYS", 7, "2025-06-02 10:05:44", None, "E017", "CHG-2025-061", "E001"),
    ("CFG-004", "CLAIM_APPROVAL_LIMIT_NON_MANAGER", 2000000, "2026-02-16 22:41:07", "2026-03-23 09:14:52", "E007", None, None),
    ("CFG-005", "CLAIM_APPROVAL_LIMIT_NON_MANAGER", 500000, "2026-03-23 09:14:52", None, "E017", "CHG-2026-031", "E001"),
]

# ---------------------------------------------------------------- write db
if os.path.exists(OUT):
    os.remove(OUT)
con = sqlite3.connect(OUT)
cur = con.cursor()
cur.executescript("""
CREATE TABLE employees (
  emp_id TEXT PRIMARY KEY, name TEXT, department TEXT, job_title TEXT,
  system_role TEXT, hire_date TEXT);
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY, customer_name TEXT, onboarded_at TEXT, onboarded_by TEXT);
CREATE TABLE skus (
  sku_id TEXT PRIMARY KEY, description TEXT, category TEXT, unit_cost INTEGER);
CREATE TABLE shipments (
  shipment_id TEXT PRIMARY KEY, customer_id TEXT, carrier TEXT, declared_value INTEGER,
  created_by TEXT, created_at TEXT);
CREATE TABLE shipment_status_log (
  log_id INTEGER PRIMARY KEY, shipment_id TEXT, status TEXT, changed_by TEXT, changed_at TEXT);
CREATE TABLE proof_of_delivery (
  pod_id TEXT PRIMARY KEY, shipment_id TEXT, delivered_at TEXT, signed_by TEXT, captured_by TEXT);
CREATE TABLE exceptions (
  exception_id TEXT PRIMARY KEY, shipment_id TEXT, exception_type TEXT,
  registered_by TEXT, registered_at TEXT, closed_by TEXT, closed_at TEXT, resolution TEXT);
CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY, shipment_id TEXT, exception_id TEXT, customer_id TEXT,
  claim_type TEXT, claim_amount INTEGER, submitted_by TEXT, submitted_at TEXT,
  approved_by TEXT, approved_at TEXT, status TEXT, rejection_reason TEXT,
  paid_amount INTEGER, paid_date TEXT);
CREATE TABLE inventory_adjustments (
  adj_id TEXT PRIMARY KEY, sku_id TEXT, qty_change INTEGER, reason TEXT,
  adjusted_by TEXT, adjusted_at TEXT, approved_by TEXT, approved_at TEXT);
CREATE TABLE system_config_history (
  config_id TEXT PRIMARY KEY, parameter TEXT, value INTEGER, effective_from TEXT,
  effective_to TEXT, changed_by TEXT, change_ticket TEXT, ticket_approved_by TEXT);
""")
cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", EMP)
cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)
cur.executemany("INSERT INTO skus VALUES (?,?,?,?)", skus)
cur.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?)",
                [(x["id"], x["customer"], x["carrier"], x["value"], x["created_by"], s(x["created_at"])) for x in shipments])
status_log.sort(key=lambda r: r[3])
cur.executemany("INSERT INTO shipment_status_log (shipment_id,status,changed_by,changed_at) VALUES (?,?,?,?)",
                [(r[0], r[1], r[2], s(r[3])) for r in status_log])
pods.sort(key=lambda p: p[1])
cur.executemany("INSERT INTO proof_of_delivery VALUES (?,?,?,?,?)",
                [(f"POD-{i:05d}", p[0], p[1], p[2], p[3]) for i, p in enumerate(pods, 1)])
cur.executemany("INSERT INTO exceptions VALUES (?,?,?,?,?,?,?,?)",
                [(e["id"], e["ship"], e["type"], e["reg_by"], s(e["reg_at"]), e["close_by"], s(e["close_at"]), e["res"]) for e in exceptions])
cur.executemany("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [(c["id"], c["ship"], c["exc"]["id"], c["cust"], c["type"], c["amt"], c["sub_by"], s(c["sub_at"]),
                  c["appr"], s(c["appr_at"]), c["status"], c["reason"], c["paid_amount"], c["paid_date"]) for c in claims])
cur.executemany("INSERT INTO inventory_adjustments VALUES (?,?,?,?,?,?,?,?)",
                [(a["id"], a["sku"], a["qty"], a["reason"], a["by"], s(a["at"]), a["appr"], s(a["appr_at"])) for a in adjs])
cur.executemany("INSERT INTO system_config_history VALUES (?,?,?,?,?,?,?,?)", config)
con.commit()
for t in ["employees", "customers", "skus", "shipments", "shipment_status_log", "proof_of_delivery",
          "exceptions", "claims", "inventory_adjustments", "system_config_history"]:
    print(f"{t:<24}{cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>7}")
con.close()
