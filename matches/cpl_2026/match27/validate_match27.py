"""
validate_match27.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 27 (Trinbago Knight Riders vs Barbados
Tridents, Kensington Oval, Bridgetown, 2026-09-05).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match27_tkr_vs_tridents.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Trinbago Knight Riders': {
        'Colin Munro': (38, 32, 3, 2, 'bowled'),
        'Sunil Narine': (2, 9, 0, 0, 'caught'),
        'Nicholas Pooran': (59, 37, 2, 7, 'caught'),
        'Kieron Pollard': (15, 13, 2, 1, 'caught'),
        'Alex Hales': (2, 4, 0, 0, 'stumped'),
        'Jyd Goolie': (3, 4, 0, 0, 'bowled'),
        'Joshua Da Silva': (10, 9, 1, 0, 'not out'),
        'Akeal Hosein': (7, 13, 0, 0, 'not out'),
    },
    'Barbados Tridents': {
        'Brandon King': (16, 13, 3, 0, 'caught'),
        'Zachary Carter': (21, 20, 4, 0, 'bowled'),
        'Quinton de Kock': (0, 1, 0, 0, 'lbw'),
        'Rivaldo Clarke': (0, 4, 0, 0, 'lbw'),
        'Chris Green': (5, 6, 1, 0, 'caught'),
        'Sherfane Rutherford': (21, 24, 2, 0, 'caught'),
        'Shadrack Descarte': (16, 9, 2, 1, 'caught'),
        'Daniel Sams': (17, 14, 0, 2, 'caught'),
        'Gudakesh Motie': (9, 11, 0, 0, 'caught'),
        'Mujeeb Ur Rahman': (4, 8, 0, 0, 'not out'),
        'Jakeem Pollard': (0, 1, 0, 0, 'caught'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures are keyed under the team that BATTED against them, i.e. the innings
# the bowler bowled in, per the toolkit's known pitfall about this)
EXPECTED_BOWLING = {
    'Trinbago Knight Riders': {  # bowled by Barbados Tridents
        'Chris Green': (4.0, 17, 0),
        'Daniel Sams': (4.0, 20, 0),
        'Jakeem Pollard': (3.0, 31, 1),
        'Mujeeb Ur Rahman': (4.0, 22, 2),
        'Shadrack Descarte': (3.0, 22, 0),
        'Gudakesh Motie': (2.0, 29, 3),
    },
    'Barbados Tridents': {  # bowled by Trinbago Knight Riders
        'Sunil Narine': (3.3, 12, 4),
        'Lahiru Kumara': (4.0, 30, 2),
        'Akeal Hosein': (3.0, 25, 1),
        'Usman Tariq': (4.0, 25, 0),
        'Jyd Goolie': (4.0, 20, 3),
    },
}

EXPECTED_EXTRAS = {
    'Trinbago Knight Riders': {'legbyes': 6, 'noballs': 1, 'wides': 4},
    'Barbados Tridents': {'wides': 3},
}


def overs_to_balls(overs_str):
    o, _, b = str(overs_str).partition('.')
    return int(o) * 6 + (int(b) if b else 0)


def main():
    d = json.load(open(JSON_PATH))
    all_ok = True

    for inn in d['innings']:
        team = inn['team']
        print(f'=== {team} (batting) ===')

        runs = defaultdict(int); balls = defaultdict(int)
        fours = defaultdict(int); sixes = defaultdict(int); outs = {}
        bowler_balls = defaultdict(int); bowler_runs = defaultdict(int); bowler_wkts = defaultdict(int)
        extras_total = defaultdict(int)

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                for k, v in ex.items():
                    extras_total[k] += v

                legal_ball = 'wides' not in ex and 'noballs' not in ex
                if 'wides' not in ex:
                    balls[b] += 1
                if legal_ball:
                    bowler_balls[bwl] += 1
                bowler_runs[bwl] += deliv['runs']['total'] - ex.get('byes', 0) - ex.get('legbyes', 0)

                if not ex or 'noballs' in ex:
                    runs[b] += deliv['runs']['batter']
                    if deliv['runs']['batter'] == 4: fours[b] += 1
                    if deliv['runs']['batter'] == 6: sixes[b] += 1

                for w in deliv.get('wickets', []):
                    outs[w['player_out']] = w['kind']
                    if w['kind'] not in ('run out', 'retired out'):
                        bowler_wkts[bwl] += 1

        print('-- Batting --')
        for name, (er, eb, ef, es, estatus) in EXPECTED_BATTING[team].items():
            ar, ab, af, aS = runs[name], balls[name], fours[name], sixes[name]
            astatus = outs.get(name, 'not out')
            ok = (ar, ab, af, aS) == (er, eb, ef, es) and estatus in astatus
            all_ok &= ok
            print(f"  {name}: got {ar}({ab}) 4s{af} 6s{aS} [{astatus}] vs expected "
                  f"{er}({eb}) 4s{ef} 6s{es} [{estatus}]", 'OK' if ok else '*** MISMATCH ***')

        print('-- Bowling --')
        for name, (eo, er, ew) in EXPECTED_BOWLING[team].items():
            got_overs = f"{bowler_balls[name] // 6}.{bowler_balls[name] % 6}"
            ok = bowler_balls[name] == overs_to_balls(eo) and bowler_runs[name] == er and bowler_wkts[name] == ew
            all_ok &= ok
            print(f"  {name}: got {got_overs}-{bowler_runs[name]}-{bowler_wkts[name]} vs expected "
                  f"{eo}-{er}-{ew}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
