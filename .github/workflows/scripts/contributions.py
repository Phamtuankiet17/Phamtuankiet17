import json, os, sys, datetime as dt, urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{firstDay contributionDays{date contributionCount contributionLevel weekday}}}}}}"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

def fetch(login, token):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "contrib-svg"})
    data = json.load(urllib.request.urlopen(req))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def demo():
    import random; random.seed(3)
    start = dt.date(2025, 10, 19); weeks = []; today = dt.date(2026, 10, 23)
    for c in range(53):
        days = []
        for r in range(7):
            d = start + dt.timedelta(days=7 * c + r)
            if d > today: continue
            n = random.choice([0, 0, 0, 1, 2, 4, 6]) if random.random() < .35 else 0
            lv = 0 if n == 0 else 1 if n < 2 else 2 if n < 4 else 3 if n < 6 else 4
            days.append({"date": d.isoformat(), "contributionCount": n, "contributionLevel": list(LEVELS)[lv], "weekday": r})
        weeks.append({"firstDay": days[0]["date"], "contributionDays": days})
    return {"totalContributions": sum(x["contributionCount"] for w in weeks for x in w["contributionDays"]), "weeks": weeks}

def fmt(d): return d.strftime("%b ") + str(d.day)
def span(a, b): return fmt(a) if a == b else f"{fmt(a)} - {fmt(b)}"

def streaks(days):
    days = sorted(days, key=lambda x: x["date"])
    best = (0, None, None); run = 0; s = None
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        if x["contributionCount"] > 0:
            if run == 0: s = d
            run += 1
            if run > best[0]: best = (run, s, d)
        else: run = 0
    cur = (0, None, None); i = len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0: i -= 1
    e = None
    while i >= 0 and days[i]["contributionCount"] > 0:
        d = dt.date.fromisoformat(days[i]["date"]); e = e or d
        cur = (cur[0] + 1, d, e); i -= 1
    return cur, best

def build(cal):
    FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    BG, PANEL, TEXT, MUTE, LINE = "#0d1117", "#161b22", "#e6edf3", "#8b949e", "#30363d"
    PW, H, GAP = 410, 170, 16; W = PW * 2 + GAP
    days = [x for w in cal["weeks"] for x in w["contributionDays"]]
    cur, best = streaks(days)
    first = dt.date.fromisoformat(days[0]["date"])
    first_c = next((dt.date.fromisoformat(x["date"]) for x in days if x["contributionCount"] > 0), first)
    cols = [(68, str(cal["totalContributions"]), "Total Contributions", f"{fmt(first)}, {first.year} - Present", TEXT, MUTE),
            (205, str(cur[0]), "Current Streak", span(cur[1], cur[2]) if cur[0] else "No active streak", "#f0883e", "#f0883e"),
            (342, str(best[0]), "Longest Streak", span(best[1], best[2]) if best[0] else "-", TEXT, MUTE)]
    b = f'<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{PW}" height="{H}" rx="8" fill="{PANEL}"/>'
    for cx, n, lab, rng, c1, c2 in cols:
        if lab == "Current Streak":
            b += f'<circle cx="{cx}" cy="70" r="36" fill="none" stroke="#f0883e" stroke-width="4" stroke-dasharray="200 26" stroke-linecap="round" transform="rotate(-70 {cx} 70)"/>'
            b += f'<path transform="translate({cx-8},26) scale(1.1)" fill="#f0883e" d="M8 0s5 3.5 5 8.5A5 5 0 0 1 3 9c0-2 1.2-3.2 2.2-4.2C6.5 3.5 8 2.4 8 0Z"/>'
            b += f'<text x="{cx}" y="80" font-size="30" font-weight="700" fill="{c1}" text-anchor="middle">{n}</text>'
            b += f'<text x="{cx}" y="128" font-size="12" font-weight="600" fill="{c1}" text-anchor="middle">{lab}</text>'
            b += f'<text x="{cx}" y="148" font-size="10.5" fill="{c2}" text-anchor="middle">{rng}</text>'
        else:
            b += f'<text x="{cx}" y="76" font-size="30" font-weight="700" fill="{c1}" text-anchor="middle">{n}</text>'
            b += f'<text x="{cx}" y="108" font-size="12" font-weight="600" fill="{TEXT}" text-anchor="middle">{lab}</text>'
            b += f'<text x="{cx}" y="128" font-size="10.5" fill="{MUTE}" text-anchor="middle">{rng}</text>'
    for lx in (137, 273): b += f'<line x1="{lx}" x2="{lx}" y1="30" y2="140" stroke="{LINE}"/>'
    X0 = PW + GAP; pal = ["#1b2129", "#0e4429", "#006d32", "#26a641", "#39d353"]
    b += f'<rect x="{X0}" width="{PW}" height="{H}" rx="8" fill="{PANEL}"/><text x="{X0+14}" y="26" font-size="11" font-weight="600" fill="{TEXT}">Contributions in the last year</text>'
    n = len(cal["weeks"]); gx, gy = X0 + 36, 70; pitch = (PW - 36 - 14) / n; cs = pitch * .82; last = None
    for c, w in enumerate(cal["weeks"]):
        d0 = dt.date.fromisoformat(w["firstDay"])
        if d0.month != last and c > 0: b += f'<text x="{gx+c*pitch:.1f}" y="60" font-size="8.5" fill="{MUTE}">{d0.strftime("%b")}</text>'
        last = d0.month
        for x in w["contributionDays"]:
            lv = LEVELS.get(x["contributionLevel"], 0)
            b += f'<rect x="{gx+c*pitch:.1f}" y="{gy+x["weekday"]*pitch:.1f}" width="{cs:.1f}" height="{cs:.1f}" rx="1.2" fill="{pal[lv]}"/>'
    for t, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)): b += f'<text x="{X0+12}" y="{gy+r*pitch+5.2:.1f}" font-size="8.5" fill="{TEXT}">{t}</text>'
    b += f'<text x="{X0+PW-112}" y="{H-12}" font-size="8.5" fill="{MUTE}">Less</text>'
    for k, c in enumerate(pal): b += f'<rect x="{X0+PW-90+k*10}" y="{H-20}" width="8" height="8" rx="1.5" fill="{c}"/>'
    b += f'<text x="{X0+PW-36}" y="{H-12}" font-size="8.5" fill="{MUTE}">More</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">{b}</svg>'

if __name__ == "__main__":
    cal = demo() if os.environ.get("DEMO") else fetch(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"])
    open(os.environ.get("OUT", "contributions.svg"), "w", encoding="utf-8").write(build(cal))
