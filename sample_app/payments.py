def authorizePayment(payment_intent):
    return {"status": "authorized", "id": payment_intent["id"]}


def sendReceipt(payment):
    return {"sent": True, "payment_id": payment["id"]}


def createPaymentIntent(amount):
    intent = {"id": "pi_demo", "amount": amount}
    return sendReceipt(authorizePayment(intent))

