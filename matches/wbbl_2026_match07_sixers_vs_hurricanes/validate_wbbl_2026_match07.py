"""
validate_wbbl_2026_match07.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27 Match 7, Sydney Sixers Women vs Hobart Hurricanes Women, 2026-11-01).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match07_sixers_vs_hurricanes.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Sydney Sixers Women': {
        'Sophia Dunkley': (0, 2, 0, 0, 'caught'),
        'Ellyse Perry': (3, 5, 0, 0, 'caught'),
        'Melie Kerr': (1, 3, 0, 0, 'caught'),
        'Ashleigh Gardner': (124, 60, 10, 9, 'caught'),
        'Alice Capsey': (54, 40, 5, 1, 'not out'),
        'Eva Ragg': (3, 4, 0, 0, 'caught'),
        'Erin Burns': (0, 1, 0, 0, 'lbw'),
        'Lauren Cheatle': (1, 3, 0, 0, 'caught'),
        'Sarah Coyte': (0, 1, 0, 0, 'caught'),
        'Caoimhe Bray': (1, 1, 0, 0, 'not out'),
    },
    'Hobart Hurricanes Women': {
        'Lizelle Lee': (5, 14, 0, 0, 'caught'),
        'Chamari Athapaththu': (10, 13, 1, 1, 'caught'),
        'Rachel Trenaman': (0, 4, 0, 0, 'bowled'),
        'Nicola Carey': (1, 4, 0, 0, 'bowled'),
        'Heather Graham': (4, 6, 0, 0, 'bowled'),
        'Maddy Green': (42, 33, 4, 0, 'not out'),
        'Chinelle Henry': (32, 20, 5, 0, 'bowled'),
        'Hayley Silver-Holmes': (2, 2, 0, 0, 'run out'),
        'Molly Strano': (0, 2, 0, 0, 'caught'),
        'Lauren Smith': (9, 7, 1, 0, 'caught'),
        'Isabella Malgioglio': (1, 2, 0, 0, 'bowled'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Sydney Sixers Women': {  # bowled by Hobart Hurricanes Women
        'Chinelle Henry': (2.0, 8, 2),
        'Nicola Carey': (4.0, 31, 3),
        'Heather Graham': (4.0, 44, 1),
        'Isabella Malgioglio': (2.0, 18, 0),
        'Hayley Silver-Holmes': (2.0, 32, 0),
        'Lauren Smith': (3.0, 29, 0),
        'Molly Strano': (3.0, 32, 2),
    },
    'Hobart Hurricanes Women': {  # bowled by Sydney Sixers Women
        'Caoimhe Bray': (4.0, 14, 2),
        'Lauren Cheatle': (4.0, 23, 1),
        'Ashleigh Gardner': (3.0, 23, 3),
        'Melie Kerr': (2.4, 25, 3),
        'Sarah Coyte': (3.0, 17, 0),
        'Frankie Nicklin': (1.0, 7, 0),
    },
}

# Scorecard (0s, WD, NB) per bowler. Cricinfo counts bye/leg-bye balls as dots.
EXPECTED_BOWLING_DETAIL = {
    'Sydney Sixers Women': {
        'Chinelle Henry': (6, 0, 0), 'Nicola Carey': (12, 3, 0), 'Heather Graham': (4, 1, 0),
        'Isabella Malgioglio': (4, 0, 0), 'Hayley Silver-Holmes': (2, 2, 0),
        'Lauren Smith': (4, 0, 0), 'Molly Strano': (4, 1, 0),
    },
    'Hobart Hurricanes Women': {
        'Caoimhe Bray': (16, 2, 0), 'Lauren Cheatle': (12, 0, 0), 'Ashleigh Gardner': (7, 0, 1),
        'Melie Kerr': (4, 0, 0), 'Sarah Coyte': (6, 0, 0), 'Frankie Nicklin': (2, 0, 0),
    },
}
SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT = {}

EXPECTED_EXTRAS = {
    'Sydney Sixers Women': {'byes': 0, 'legbyes': 2, 'noballs': 0, 'wides': 7},
    'Hobart Hurricanes Women': {'byes': 0, 'legbyes': 0, 'noballs': 1, 'wides': 2},
}

# (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Sydney Sixers Women', 'Sophia Dunkley'): ['Chamari Athapaththu'],
    ('Sydney Sixers Women', 'Ellyse Perry'): ['Lauren Smith'],
    ('Sydney Sixers Women', 'Melie Kerr'): ['Maddy Green'],
    ('Sydney Sixers Women', 'Ashleigh Gardner'): ['Chinelle Henry'],
    ('Sydney Sixers Women', 'Eva Ragg'): ['Chinelle Henry'],
    ('Sydney Sixers Women', 'Lauren Cheatle'): ['Lauren Smith'],
    ('Sydney Sixers Women', 'Sarah Coyte'): ['Lauren Smith'],
    ('Hobart Hurricanes Women', 'Lizelle Lee'): ['Lauren Cheatle'],
    ('Hobart Hurricanes Women', 'Chamari Athapaththu'): ['Erin Burns'],
    ('Hobart Hurricanes Women', 'Hayley Silver-Holmes'): ['Caoimhe Bray', 'Ashleigh Gardner'],
    ('Hobart Hurricanes Women', 'Molly Strano'): ['Ellyse Perry'],
    ('Hobart Hurricanes Women', 'Lauren Smith'): ['Ellyse Perry'],
}

EXPECTED_TOTALS = {'Sydney Sixers Women': (196, 8), 'Hobart Hurricanes Women': (109, 10)}


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
        fielders_got = {}
        bdet = defaultdict(lambda: [0, 0, 0])
        tot = sum(x['runs']['total'] for o in inn['overs'] for x in o['deliveries'])
        wk = sum(len(x.get('wickets', [])) for o in inn['overs'] for x in o['deliveries'])

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                bdet[bwl][0] += deliv['runs']['batter'] == 0 and set(ex) <= {'legbyes', 'byes'}
                bdet[bwl][1] += ex.get('wides', 0) > 0
                bdet[bwl][2] += ex.get('noballs', 0) > 0
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
                    fielders_got[w['player_out']] = [f['name'] for f in w.get('fielders', [])]
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

        print('-- Bowler 0s/WD/NB --')
        for name, e in EXPECTED_BOWLING_DETAIL[team].items():
            ok = tuple(bdet[name]) == e
            all_ok &= ok
            note = (f" (scorecard prints {SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT[name]} dots - known inconsistent)"
                    if name in SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT else '')
            print(f"  {name}: got {tuple(bdet[name])} vs expected {e}{note}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Fielders / total --')
        for (t, pl), ef in EXPECTED_FIELDERS.items():
            if t != team: continue
            ok = fielders_got.get(pl) == ef
            all_ok &= ok
            print(f"  {pl}: got {fielders_got.get(pl)} vs expected {ef}", 'OK' if ok else '*** MISMATCH ***')
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"  total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
