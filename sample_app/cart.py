def validateCart(cart):
    return bool(cart.get("items"))


def addItem(cart, item):
    cart["items"].append(item)
    return updateCartTotal(cart)


def removeItem(cart, product_id):
    cart["items"] = [item for item in cart["items"] if item["id"] != product_id]
    return updateCartTotal(cart)


def updateCartTotal(cart):
    cart["total"] = sum(item["price"] * item["quantity"] for item in cart["items"])
    return cart["total"]

