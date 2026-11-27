extends RefCounted
## Durable public stock, displayed offer and earned cash for the walk-up counter.

const PRODUCTS := ["meal", "planks", "blocks"]
const MATERIAL_PRODUCTS := {"planks": 0, "blocks": 0}
const SOLD := {"meal": 0, "planks": 0, "blocks": 0}
const PRICES := {"meal": 1, "planks": 2, "blocks": 2}
const EMPTY := {
	"counter_products": MATERIAL_PRODUCTS,
	"worker_products": MATERIAL_PRODUCTS,
	"construction_products": MATERIAL_PRODUCTS,
	"sold": SOLD,
	"order": {},
	"earned": 0,
	"counter_cash": 0,
	"worker_cash": 0,
}

static func from_single_meal(journal: Dictionary) -> Variant:
	for key: String in ["served", "pocket_cash", "house_cash"]:
		if not count(journal.get(key)): return null
	var proceeds := int(journal.served) - int(journal.pocket_cash) - int(journal.house_cash)
	if proceeds < 0: return null
	var market: Dictionary = EMPTY.duplicate(true)
	market.sold.meal = int(journal.served)
	market.earned = int(journal.served)
	market.counter_cash = proceeds
	return market

static func count(amount: Variant) -> bool:
	return (amount is int or amount is float) and is_finite(float(amount)) and amount == int(amount) and amount >= 0

static func normalize(market: Dictionary) -> void:
	for column: String in ["counter_products", "worker_products", "construction_products", "sold"]:
		for kind in market[column]:
			market[column][kind] = int(market[column][kind])
	for key: String in ["earned", "counter_cash", "worker_cash"]:
		market[key] = int(market[key])
	if market.order.is_empty(): return
	market.order.id = int(market.order.id)
	market.order.price = int(market.order.price)
	for kind in market.order.goods:
		market.order.goods[kind] = int(market.order.goods[kind])

static func valid(journal: Dictionary, restored_cash: int, worker_limit: int) -> bool:
	var market: Variant = journal.get("market")
	if not market is Dictionary or market.size() != EMPTY.size() or not market.has_all(EMPTY.keys()): return false
	for column: String in ["counter_products", "worker_products", "construction_products", "sold"]:
		var goods: Variant = market[column]
		if not goods is Dictionary or goods.size() != EMPTY[column].size() or not goods.has_all(EMPTY[column].keys()): return false
		for kind in goods:
			if not count(goods[kind]): return false
			if column == "worker_products" and (goods[kind] > worker_limit or goods[kind] > 0 and not journal.rescued): return false
	for key: String in ["earned", "counter_cash", "worker_cash"]:
		if not count(market[key]): return false
	if market.worker_cash > 0 and not journal.rescued: return false
	if market.earned != price(market.sold): return false
	var total_sold: int = int(market.sold.meal) + int(market.sold.planks) + int(market.sold.blocks)
	if int(journal.served) > total_sold or total_sold > int(journal.served)*3: return false
	if int(market.earned) != int(market.counter_cash) + int(market.worker_cash) + restored_cash: return false
	var order: Variant = market.order
	return order is Dictionary and (order.is_empty() or valid_order(order, int(journal.served) + 1))

static func valid_order(order: Dictionary, id: int) -> bool:
	if order.size() != 3 or not order.has_all(["id", "price", "goods"]) or order.id != id or not order.goods is Dictionary: return false
	if order.goods.is_empty() or order.goods.size() > PRODUCTS.size() or not count(order.price): return false
	var quantity := 0
	for kind in order.goods:
		if kind not in PRODUCTS or not count(order.goods[kind]) or order.goods[kind] < 1 or order.goods[kind] > 2: return false
		quantity += int(order.goods[kind])
	return quantity <= 3 and order.price == price(order.goods)

static func price(goods: Dictionary) -> int:
	var sum := 0
	for kind in goods:
		sum += int(goods[kind]) * int(PRICES[kind])
	return sum

static func is_meal_order(order: Dictionary) -> bool:
	var goods: Variant = order.get("goods")
	return goods is Dictionary and goods.size() == 1 and goods.has("meal")

static func new_order(id: int, portions: int) -> Dictionary:
	return {"id": id, "goods": {"meal": portions}, "price": portions * PRICES.meal}

static func available(journal: Dictionary, kind: String) -> int:
	return int(journal.counter_stock) if kind == "meal" else int(journal.market.counter_products[kind])

static func add_to_counter(journal: Dictionary, kind: String, amount: int) -> void:
	if kind == "meal": journal.counter_stock += amount
	else: journal.market.counter_products[kind] += amount

static func worker_stock(journal: Dictionary, kind: String) -> int:
	return int(journal.worker_meal) if kind == "meal" else int(journal.market.worker_products[kind])

static func add_to_worker(journal: Dictionary, kind: String, amount: int) -> void:
	if kind == "meal": journal.worker_meal += amount
	else: journal.market.worker_products[kind] += amount

static func can_fill(journal: Dictionary, order: Dictionary) -> bool:
	if order.is_empty(): return false
	return order.goods.keys().all(func(kind): return available(journal, kind) >= int(order.goods[kind]))

static func sell(journal: Dictionary, id: int) -> bool:
	var market: Dictionary = journal.market
	var order: Dictionary = market.order
	if not valid_order(order, id) or not is_meal_order(order) or id != int(journal.served) + 1 or not can_fill(journal, order): return false
	for kind in order.goods:
		var quantity := int(order.goods[kind])
		add_to_counter(journal, kind, -quantity)
		market.sold[kind] += quantity
	market.counter_cash += int(order.price)
	market.earned += int(order.price)
	market.order = {}
	journal.served += 1
	return true
