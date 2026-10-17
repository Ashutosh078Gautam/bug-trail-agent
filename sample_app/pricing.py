def loadProduct(product_id):
    return {"id": product_id, "price": 100.0}


def getCustomerTier(customer):
    return customer.get("tier", "standard")


def calculateSubtotal(items):
    return sum(item["price"] * item["quantity"] for item in items)


def applyCoupon(subtotal, coupon):
    if not coupon:
        return subtotal
    if coupon.get("type") == "percentage":
        return subtotal * (1 - coupon["value"] / 100)
    return subtotal - coupon.get("value", 0)


def isTaxable(item):
    return item.get("taxable", True)


def calculateTax(items):
    taxable_total = sum(item["price"] * item["quantity"] for item in items if isTaxable(item))
    return taxable_total * 0.18


def roundMoney(amount):
    return round(amount, 2)


def formatCurrency(amount):
    return f"₹{roundMoney(amount):.2f}"


def calculateTotal(items, coupon=None):
    subtotal = calculateSubtotal(items)
    discounted = applyCoupon(subtotal, coupon)
    return roundMoney(discounted + calculateTax(items))

