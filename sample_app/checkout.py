from sample_app.cart import validateCart
from sample_app.payments import createPaymentIntent
from sample_app.pricing import applyCoupon, calculateSubtotal


def buildOrderSummary(items, total):
    return {"items": items, "total": total}


def checkout(cart, coupon=None):
    validateCart(cart)
    subtotal = calculateSubtotal(cart["items"])
    total = applyCoupon(subtotal, coupon)
    createPaymentIntent(total)
    return buildOrderSummary(cart["items"], total)

