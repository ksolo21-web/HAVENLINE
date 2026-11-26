"""Narrow mechanical wrapper patch. No game bytes read or rewritten here."""
from pathlib import Path
from hashlib import sha256
import sys
p=Path(sys.argv[1]); f=p.read_bytes()
assert sha256(f).hexdigest()==sys.argv[2], "unexpected exact V2 wrapper SHA"
s=f.decode()
start=s.index('  timeout 180 env -i ')
end=s.index('\n  grep -q',start)
old=s[start:end]
assert old.endswith('> "$out/$phase.log" 2>&1')
run=old.strip().replace('timeout 180 env -i ','timeout "$deadline" env -i ',1)
new='''  local deadline=180 rc=0 started ended
  [[ "$phase" != write ]] || deadline=360
  started="$(date +%s)"
  printf '{"event":"start","phase":"%s","deadline_s":%d,"unix_s":%s}\n' "$phase" "$deadline" "$started" >> "$out/exec-phase-status.jsonl"
  if '''+ run +'''; then
    rc=0
  else
    rc=$?
  fi
  ended="$(date +%s)"
  printf '{"event":"exit","phase":"%s","deadline_s":%d,"unix_s":%s,"elapsed_s":%d,"exit_status":%d}\n' "$phase" "$deadline" "$ended" "$((ended-started))" "$rc" >> "$out/exec-phase-status.jsonl"
  if ((rc!=0)); then
    printf 'exec_phase %s failed (status %d, deadline %ss); see %s\n' "$phase" "$rc" "$deadline" "$out/exec-phase-status.jsonl" >&2
    return "$rc"
  fi'''
# Emit literal Bash backslash-n instead of multiline quote formatting.
new=new.replace("\n' \"","\\n' \"")
assert s.count(old)==1
sys.stdout.write(s[:start]+new+s[end:])
