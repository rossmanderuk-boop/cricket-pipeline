# Cricinfo Commentary → Cricsheet JSON

This repo converts pasted ESPN Cricinfo ball-by-ball commentary (plus a scorecard) into
Cricsheet-format match JSON (`info`/`innings` structure), for CPL and other T20 matches not
yet in an official Cricsheet release.

## Workflow

1. Get the input: ball-by-ball commentary (usually one block per innings) and, ideally, the
   official scorecard text. If only commentary is pasted with no scorecard, ask for the
   scorecard before proceeding — validation is not optional. If commentary for only one
   innings is pasted, ask whether the other innings is coming.

2. Split into one file per innings: save each innings' commentary to its own file
   (e.g. `matches/matchNN/innings1.txt`, `innings2.txt`). This is a hard rule — commentary
   that shares over-numbering between two innings is the easiest way to misattribute a
   delivery to the wrong team. Figure out which innings is which from context (which team is
   batting/bowling, "Need N runs" chase language, etc.).

   Leave prose/flavour text in the file if convenient; the parser
   (`scripts/parse_cricinfo.py`) ignores anything that doesn't match its patterns. Every
   delivery must keep its three key lines: the `over.ball` marker, the result marker
   (optional, ignored), and the `Bowler to Batter, <description>` line — and for wickets, the
   compact dismissal detail line (`Player c Fielder b Bowler N (Mb ...)`) within the next
   several lines.

3. Copy `scripts/build_match_json_template.py` to a per-match script
   (`matches/matchNN/build_matchNN.py` — don't edit the template in place). Fill in the
   `CONFIG` section: team names, playing XIs (from the scorecard's batting list + "Did not
   bat"), match info (date, venue, toss if known, outcome, season, match number, player of
   the match), and critically the `NAME_MAP` — every short/alternate name used in the
   commentary mapped to one canonical full name, with identity mappings for the full names
   too. Get this wrong and a wicket silently fails to attach to the right player's batting
   figures. Cross-reference both innings' bowling cards against the "Did not bat" lists to
   build the XI + NAME_MAP — the bowlers of one team's innings and the "did not bat" list of
   the other team should agree.

4. Run it to produce the match JSON, and read the sanity-check totals it prints (each
   innings' summed total).

5. Validate — always, before treating a match as done. Write a short validation script that
   reconstructs, from the JSON, every batter's runs/balls/4s/6s/dismissal and every bowler's
   overs/runs/wickets/economy, and diffs them against the scorecard exactly. Also check
   extras (byes/leg byes/wides/no-balls) per innings.

   A completely clean first pass is worth being suspicious of — at least one round of
   "parse → validate → find a mismatch → fix → re-validate" is normal. Common mismatches:
   - Total runs match but individual figures don't → usually a `NAME_MAP` gap.
   - A wicket recorded as "not out" even though commentary clearly describes a dismissal →
     the dismissal detail line wasn't found; Cricinfo sometimes inserts a prose paragraph
     between the `OUT` line and the compact detail line — the parser already scans forward
     past prose for this, but extend it if new phrasing appears.
   - A bowler's overs off by fractions of a ball → check the *validation script's* arithmetic
     first — wides AND no-balls are excluded from legal-ball count, but a no-ball's free-hit
     retry DOES count.
   - Bowler figures all zero → check the validation script's expected-figures dict is keyed
     under the *batting* team, not the bowling team.

   Only hand back the JSON once every batter, every bowler, and both innings' extras/totals
   match.

6. Commit the final JSON (e.g. `matches/matchNN/cpl_2026_matchNN_TEAMA_vs_TEAMB.json`) and
   the per-match build/validation scripts to the repo. Note anything assumed (e.g. toss
   winner/decision if not stated) so it can be corrected.

## Known edge cases the parser already handles

- Wide + retry sharing the same `over.ball` label (a wide doesn't advance the ball count).
- No-ball with runs scored off it — recorded as `extras.noballs: 1` plus `runs.batter: N`.
  The free-hit retry is a normal legal delivery.
- A wicket credited to a different player than the one facing the ball (e.g. non-striker run
  out) — parser strips trailing `, OUT` and parses runs/extras normally, then separately
  resolves the named dismissed player.
- `c & b`, `lbw b`, `run out (Fielder)`, multi-fielder run outs (`Fielder1/Fielder2`),
  `st Fielder b Bowler`, and the wicketkeeper `†` dagger symbol.
- Dismissal detail lines separated from the `OUT` marker by a prose paragraph.

## What still needs doing by hand, per match

- `NAME_MAP` — always, every match, by reading both innings' commentary and dismissal lines
  and the scorecard side by side.
- D/L-affected matches — set `outcome.method: "D/L"` if the target was revised.
- Abandoned matches with no ball bowled — don't build a JSON.
