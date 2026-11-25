#!/usr/bin/env python3
"""Generate a copy for fixture dependency injection, never overwrite opening.gd."""
import sys,subprocess,hashlib
from pathlib import Path
p=Path(sys.argv[1]); src=p/"previews/integrated_opening.gd"
raw=src.read_bytes()
assert subprocess.check_output(["git","hash-object",str(src)]).decode().strip()=="ca88b482831e0898b488be6efa63caf691f2eb95"
assert subprocess.check_output(["git","hash-object",str(p/"opening_ledger.gd")]).decode().strip()=="2e713651f3a75a45db6e6577e48f7361ad37e127"
old=raw.decode()
statement="var next := Ledger.new()"
assert old.count(statement)==2
new=old.replace(statement,"var next := _fixture_next_ledger()")
helper="\nfunc _fixture_next_ledger() -> Ledger:\n\treturn Ledger.new()\n"
assert new.replace("var next := _fixture_next_ledger()",statement)==old
path=p/"fixtures/pine_store/under_test.gd"
path.write_text(new+helper)
assert raw==src.read_bytes()
