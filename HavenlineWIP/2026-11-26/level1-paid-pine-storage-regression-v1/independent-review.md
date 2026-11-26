# Independent review

The source-pinned in-memory replay reproduced the archived valid checkpoint digest and the six balance rejections. The original malformed-envelope control appends bytes to the JSON; it is not a pure hash test. A separate reviewer used a structured in-memory envelope with its recorded digest replaced by zeros and confirmed the model rejected it without changing its sentinel state. This does not demonstrate Godot parser parity, native transaction stages, or a real receiver.
