import re

DISMISSAL_RE = re.compile(
    r'^([A-Za-z .\'-]+?)\s+'
    r'(c & b|c and b|c sub \([A-Za-z .\'†-]+?\) b|c \(?sub\)?[A-Za-z .\'†-]*? b|'
    r'c [A-Za-z .\'†-]+? b|lbw b|run out ?\([A-Za-z .\'†/-]*\)|st [A-Za-z .\'†-]+? b|b)\s*'
    r'([A-Za-z .\'-]*?)\s*(\d+)\s*\((\d+)b'
)

def parse_dismissal_line(line):
    """Parse a line like 'Kamil Pooran c Toppin b Usman Tariq 25 (17b 5x4 0x6 25m) SR: 147.05'
    or 'Matthew Nandu retired out 13 (21b 0x4 0x6 46m) SR: 61.9'"""
    line = line.replace('†', '')  # strip wicketkeeper dagger symbol

    m_retired = re.match(r'^([A-Za-z .\'-]+?)\s+retired out\s+(\d+)\s*\((\d+)b', line.strip())
    if m_retired:
        player, runs, balls = m_retired.groups()
        return {'kind': 'retired out', 'player_out': player.strip(), 'fielder': None}

    m = DISMISSAL_RE.match(line.strip())
    if not m:
        return None
    player, kindtxt, bowler, runs, balls = m.groups()
    player = player.strip()
    bowler = bowler.strip()
    kindtxt = kindtxt.strip()
    if kindtxt in ('c & b', 'c and b'):
        return {'kind': 'caught and bowled', 'player_out': player, 'fielder': None}
    if kindtxt.startswith('c ') and kindtxt.endswith(' b'):
        fielder = kindtxt[2:-2].strip()
        # "c sub (Real Name) b Bowler" - substitute fielder, real name given in parens
        sub_m = re.match(r'^sub\s*\(([^)]+)\)$', fielder)
        if sub_m:
            return {'kind': 'caught', 'player_out': player, 'fielder': sub_m.group(1).strip(),
                    'substitute': True}
        fielder = fielder.replace('(sub)', '').strip()
        return {'kind': 'caught', 'player_out': player, 'fielder': fielder}
    if kindtxt == 'lbw b':
        return {'kind': 'lbw', 'player_out': player, 'fielder': None}
    if kindtxt.startswith('run out'):
        fm = re.search(r'\(([^)]+)\)', kindtxt)
        fielder = fm.group(1) if fm else None
        return {'kind': 'run out', 'player_out': player, 'fielder': fielder}
    if kindtxt.startswith('st '):
        fielder = kindtxt[3:].replace(' b', '').strip()
        return {'kind': 'stumped', 'player_out': player, 'fielder': fielder}
    if kindtxt == 'b':
        return {'kind': 'bowled', 'player_out': player, 'fielder': None}
    return None


def parse_deliveries(text):
    lines = [l for l in text.split('\n')]
    deliveries = []
    ball_re = re.compile(r'^(\d+)\.(\d+)$')
    bare_num_re = re.compile(r'^(\d+)$')
    delivery_re = re.compile(r'^([A-Za-z .\'-]+?) to ([A-Za-z .\'-]+?), (.+)$')

    i = 0
    last_over_seen = 0
    while i < len(lines):
        line = lines[i].strip()
        m = ball_re.match(line)
        bare = bare_num_re.match(line) if not m else None
        if m or bare:
            if m:
                over_no, ball_no = int(m.group(1)), int(m.group(2))
                last_over_seen = over_no
            else:
                over_no, ball_no = 0, 0
            j = i + 1
            desc_line = None
            while j < len(lines) and j < i + 4:
                cand = lines[j].strip()
                if not cand:
                    j += 1
                    continue
                dm = delivery_re.match(cand)
                if dm:
                    desc_line = cand
                    break
                j += 1
            if desc_line:
                dm = delivery_re.match(desc_line)
                bowler, batter, desc = dm.group(1).strip(), dm.group(2).strip(), dm.group(3).strip()
                d = parse_one(over_no, ball_no, bowler, batter, desc)
                if d['is_wicket']:
                    k = j + 1
                    limit = min(len(lines), j + 12)
                    while k < limit:
                        cand2 = lines[k].strip()
                        if cand2:
                            if ball_re.match(cand2) or bare_num_re.match(cand2):
                                break
                            wk = parse_dismissal_line(cand2)
                            if wk:
                                d['wicket'] = wk
                                break
                        k += 1
                deliveries.append(d)
            i = j + 1
        else:
            i += 1
    return deliveries


def parse_one(over_no, ball_no, bowler, batter, desc):
    d = {'over': over_no, 'ball': ball_no, 'bowler': bowler, 'batter': batter,
         'runs_batter': 0, 'extra_type': None, 'extra_runs': 0, 'wicket': None, 'is_wicket': False}
    desc_l = desc.lower().strip()

    is_wicket = (desc_l == 'out' or ', out' in desc_l)
    if is_wicket:
        d['is_wicket'] = True
        pre = re.sub(r',?\s*out\s*$', '', desc_l).strip()
        if pre == '' or pre == ',':
            return d
        desc_l = pre

    mm = re.match(r'\(no ball\)\s*(.*)$', desc_l)
    if mm:
        d['extra_type'] = 'noballs'
        d['extra_runs'] = 1
        rest = mm.group(1).strip()
        if rest == 'no run' or rest == '':
            d['runs_batter'] = 0
        elif rest.startswith('four'):
            d['runs_batter'] = 4
        elif rest.startswith('six'):
            d['runs_batter'] = 6
        else:
            rm = re.match(r'(\d+)\s*runs?$', rest)
            if rm:
                d['runs_batter'] = int(rm.group(1))
        return d

    mm = re.match(r'(\d+)?\s*wides?$', desc_l)
    if mm:
        d['extra_type'] = 'wides'
        d['extra_runs'] = int(mm.group(1)) if mm.group(1) else 1
        return d

    mm = re.match(r'(\d+)\s*leg byes?$', desc_l)
    if mm:
        d['extra_type'] = 'legbyes'
        d['extra_runs'] = int(mm.group(1))
        return d

    mm = re.match(r'(\d+)\s*byes?$', desc_l)
    if mm:
        d['extra_type'] = 'byes'
        d['extra_runs'] = int(mm.group(1))
        return d

    if desc_l == 'no run':
        d['runs_batter'] = 0
        return d
    if desc_l.startswith('four'):
        d['runs_batter'] = 4
        return d
    if desc_l.startswith('six'):
        d['runs_batter'] = 6
        return d
    mm = re.match(r'(\d+)\s*runs?$', desc_l)
    if mm:
        d['runs_batter'] = int(mm.group(1))
        return d

    return d
