extends RefCounted
## Nonnegative arbitrary-length decimal counts. No float/int conversion of stock.

static func valid(value: Variant) -> bool:
	if not value is String or value.is_empty():
		return false
	if value.length() > 1 and value.begins_with("0"):
		return false
	for i in range(value.length()):
		if value.unicode_at(i) < 48 or value.unicode_at(i) > 57:
			return false
	return true

static func compare(a: String, b: String) -> int:
	assert(valid(a) and valid(b))
	if a.length() != b.length():
		return 1 if a.length() > b.length() else -1
	if a == b:
		return 0
	return 1 if a > b else -1

static func add(a: String, b: String) -> String:
	assert(valid(a) and valid(b))
	var result := ""
	var carry := 0
	var i := a.length() - 1
	var j := b.length() - 1
	while i >= 0 or j >= 0 or carry > 0:
		var digit := carry
		if i >= 0:
			digit += a.unicode_at(i) - 48
		if j >= 0:
			digit += b.unicode_at(j) - 48
		result = str(digit % 10) + result
		carry = digit / 10
		i -= 1
		j -= 1
	return result

static func subtract(a: String, b: String) -> String:
	assert(valid(a) and valid(b) and compare(a, b) >= 0)
	var result := ""
	var borrow := 0
	var j := b.length() - 1
	for i in range(a.length() - 1, -1, -1):
		var digit := a.unicode_at(i) - 48 - borrow
		if j >= 0:
			digit -= b.unicode_at(j) - 48
		borrow = 0
		if digit < 0:
			digit += 10
			borrow = 1
		result = str(digit) + result
		j -= 1
	while result.length() > 1 and result.begins_with("0"):
		result = result.substr(1)
	return result

static func canonical(value: Variant) -> String:
	# JSON parses metadata numbers as floats. Canonicalize exactly representable
	# integral metadata identically; inventory quantities remain strings forever.
	if value is float and is_finite(value) and absf(value) <= 9007199254740991 and floor(value) == value:
		return str(int(value))
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var pairs: Array[String] = []
		for key in keys:
			pairs.append(JSON.stringify(key) + ":" + canonical(value[key]))
		return "{" + ",".join(pairs) + "}"
	if value is Array:
		var items: Array[String] = []
		for item in value:
			items.append(canonical(item))
		return "[" + ",".join(items) + "]"
	return JSON.stringify(value)

static func normalize_json(value: Variant) -> Variant:
	if value is float and is_finite(value) and absf(value) <= 9007199254740991 and floor(value) == value:
		return int(value)
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value: result[key] = normalize_json(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item in value: result.append(normalize_json(item))
		return result
	return value
