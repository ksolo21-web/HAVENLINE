"""JSON-safe native grammar for the existing T10 source-review response contract."""
from __future__ import annotations
import json
import re


def review_grammar(schema: dict) -> str:
    """Encode syntax only; all scoring and semantic gates remain unchanged.

    The pinned schema converter expands the sentence dot-pattern to raw quotes
    and backslashes as well as prose. Explicit JSON-safe string units prevent
    those bytes from terminating a string. No response is repaired or rescored.
    """
    fields = ['observations', 'defects', 'coverage_complete', 'confidence', 'scores']
    if not isinstance(schema, dict) or schema.get('type') != 'object' or schema.get('required') != fields or schema.get('additionalProperties') is not False:
        raise ValueError('unexpected source-review object contract')
    p = schema.get('properties', {})
    if set(p) != set(fields):
        raise ValueError('unexpected source-review fields')
    item = {'type': 'string', 'maxLength': 220, 'minLength': 1, 'pattern': '^.{0,219}[.!?]$'}
    if p['observations'] != {'type': 'array', 'items': item, 'minItems': 3, 'maxItems': 3}:
        raise ValueError('observation contract changed')
    if p['defects'] != {'type': 'array', 'items': item, 'maxItems': 5}:
        raise ValueError('defect contract changed')
    if p['coverage_complete'] != {'type': 'boolean'} or p['confidence'] != {'type': 'string', 'enum': ['low', 'medium', 'high']}:
        raise ValueError('coverage or confidence contract changed')
    spec = p['scores']
    dims = spec.get('required')
    if spec.get('type') != 'object' or spec.get('additionalProperties') is not False or not isinstance(dims, list) or not dims or len(set(dims)) != len(dims):
        raise ValueError('invalid dimension contract')
    if any(not isinstance(d, str) or re.fullmatch(r'[a-z][a-z0-9_]*', d) is None for d in dims):
        raise ValueError('unsafe dimension identifier')
    if spec.get('properties') != {d: {'type': 'number', 'minimum': 0, 'maximum': 10} for d in dims}:
        raise ValueError('score domain changed')

    def key(k: str) -> str:
        return json.dumps(json.dumps(k)) + ' ws ":" ws '

    root = 'root ::= "{" ws ' + ' "," ws '.join(key(k) + {'observations': 'observations', 'defects': 'defects', 'coverage_complete': 'boolean', 'confidence': 'confidence', 'scores': 'scores'}[k] for k in fields) + ' "}" ws'
    scores = 'scores ::= "{" ws ' + ' "," ws '.join(key(d) + 'number' for d in dims) + ' "}" ws'
    # JSON-safe character rule follows the pinned b10809 JSON grammar.
    # Syntax admits numerical low scores; the unchanged validator grades them.
    tail = r'''observations ::= "[" ws sentence "," ws sentence "," ws sentence "]" ws
 defects ::= "[" ws (sentence ("," ws sentence){0,4})? "]" ws
 sentence ::= "\"" char{0,219} [.!?] "\"" ws
 char ::= [^"\\\x7F\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F]{4})
 boolean ::= ("true" | "false") ws
 confidence ::= ("\"low\"" | "\"medium\"" | "\"high\"") ws
 number ::= ("-"? integral) ("." [0-9]{1,16})? ([eE] [-+]? integral)? ws
 integral ::= [0] | [1-9] [0-9]{0,15}
 ws ::= | " " | "\n"{1,2} [ \t]{0,20}
'''
    return root + '\n' + scores + '\n' + '\n'.join(line.lstrip() for line in tail.splitlines()) + '\n'
