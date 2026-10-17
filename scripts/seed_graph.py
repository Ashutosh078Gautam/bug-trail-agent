import sys
from pathlib import Path

# Make the project root importable when this file is run directly with
# `python scripts\\seed_graph.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph import BugTrailGraph


def main() -> None:
    db = BugTrailGraph()
    # GRAPH.DELETE fails on a graph that has never been created. Clearing via
    # Cypher works for both first-run and repeat-run seeding.
    db.query("MATCH (n) DETACH DELETE n")
    db.query(
        """
        CREATE
        (:Module {name:'checkout'}), (:Module {name:'pricing'}), (:Module {name:'cart'}),
        (:Module {name:'payments'}),
        (:Developer {name:'Priya'}), (:Developer {name:'Mateo'}), (:Developer {name:'Aisha'}),
        (:Function {name:'checkout', keywords:'checkout,order,total'}),
        (:Function {name:'validateCart', keywords:'cart,validate,items'}),
        (:Function {name:'calculateSubtotal', keywords:'subtotal,total,price'}),
        (:Function {name:'applyCoupon', keywords:'coupon,discount,percentage,applied'}),
        (:Function {name:'calculateTax', keywords:'tax,taxable,charge'}),
        (:Function {name:'calculateTotal', keywords:'total,amount,price,checkout'}),
        (:Function {name:'formatCurrency', keywords:'currency,rounding,format'}),
        (:Function {name:'removeItem', keywords:'remove,item,cart,update'}),
        (:Function {name:'addItem', keywords:'add,item,cart'}),
        (:Function {name:'updateCartTotal', keywords:'cart,total,update'}),
        (:Function {name:'createPaymentIntent', keywords:'payment,charge'}),
        (:Function {name:'authorizePayment', keywords:'payment,authorize'}),
        (:Function {name:'sendReceipt', keywords:'receipt,email'}),
        (:Function {name:'loadProduct', keywords:'product,price'}),
        (:Function {name:'getCustomerTier', keywords:'customer,discount'}),
        (:Function {name:'isTaxable', keywords:'tax,taxable'}),
        (:Function {name:'roundMoney', keywords:'rounding,money,percentage'}),
        (:Function {name:'buildOrderSummary', keywords:'order,summary'}),
        (:Test {name:'coupon percentage regression test'}),
        (:Test {name:'tax once regression test'}),
        (:Test {name:'cart removal regression test'})
        """
    )
    db.query(
        """
        MATCH
        (checkout:Function {name:'checkout'}), (validate:Function {name:'validateCart'}),
        (subtotal:Function {name:'calculateSubtotal'}), (coupon:Function {name:'applyCoupon'}),
        (tax:Function {name:'calculateTax'}), (total:Function {name:'calculateTotal'}),
        (format:Function {name:'formatCurrency'}), (remove:Function {name:'removeItem'}),
        (update:Function {name:'updateCartTotal'}), (payment:Function {name:'createPaymentIntent'}),
        (auth:Function {name:'authorizePayment'}), (receipt:Function {name:'sendReceipt'}),
        (product:Function {name:'loadProduct'}), (tier:Function {name:'getCustomerTier'}),
        (taxable:Function {name:'isTaxable'}), (round:Function {name:'roundMoney'}),
        (summary:Function {name:'buildOrderSummary'})
        CREATE
        (checkout)-[:CALLS]->(validate), (checkout)-[:CALLS]->(subtotal),
        (checkout)-[:CALLS]->(coupon), (coupon)-[:CALLS]->(tier),
        (coupon)-[:CALLS]->(total), (subtotal)-[:CALLS]->(product),
        (total)-[:CALLS]->(tax), (total)-[:CALLS]->(format),
        (tax)-[:CALLS]->(taxable), (format)-[:CALLS]->(round),
        (remove)-[:CALLS]->(update), (checkout)-[:CALLS]->(payment),
        (payment)-[:CALLS]->(auth), (auth)-[:CALLS]->(receipt),
        (checkout)-[:CALLS]->(summary),
        (checkout)-[:BELONGS_TO]->(:Module {name:'checkout'}),
        (validate)-[:BELONGS_TO]->(:Module {name:'cart'}),
        (subtotal)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (coupon)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (tax)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (total)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (format)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (remove)-[:BELONGS_TO]->(:Module {name:'cart'}),
        (update)-[:BELONGS_TO]->(:Module {name:'cart'}),
        (payment)-[:BELONGS_TO]->(:Module {name:'payments'}),
        (auth)-[:BELONGS_TO]->(:Module {name:'payments'}),
        (receipt)-[:BELONGS_TO]->(:Module {name:'payments'}),
        (product)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (tier)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (taxable)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (round)-[:BELONGS_TO]->(:Module {name:'pricing'}),
        (summary)-[:BELONGS_TO]->(:Module {name:'checkout'})
        """
    )
    db.query(
        """
        MATCH (priya:Developer {name:'Priya'}), (mateo:Developer {name:'Mateo'}), (aisha:Developer {name:'Aisha'}),
        (coupon:Function {name:'applyCoupon'}), (tax:Function {name:'calculateTax'}),
        (remove:Function {name:'removeItem'}), (round:Function {name:'roundMoney'}),
        (tc:Test {name:'coupon percentage regression test'}),
        (tt:Test {name:'tax once regression test'}), (tr:Test {name:'cart removal regression test'})
        CREATE
        (c1:Commit {id:'abc123', message:'Support percentage coupons', timestamp:'2026-10-10'})-[:AUTHORED_BY]->(priya),
        (c2:Commit {id:'def456', message:'Refactor tax calculation', timestamp:'2026-10-11'})-[:AUTHORED_BY]->(mateo),
        (c3:Commit {id:'ghi789', message:'Optimize cart item removal', timestamp:'2026-10-12'})-[:AUTHORED_BY]->(aisha),
        (c4:Commit {id:'fix901', message:'Round percentage discounts correctly', timestamp:'2026-10-13'})-[:AUTHORED_BY]->(priya),
        (coupon)-[:CHANGED_IN]->(c1), (tax)-[:CHANGED_IN]->(c2), (remove)-[:CHANGED_IN]->(c3),
        (round)-[:CHANGED_IN]->(c4)
        """
    )
    db.query("CREATE (:Bug {id:'seed-coupon-bug', description:'Percentage coupon discount is rounded incorrectly', created_at:'2026-10-09'})")
    db.query("CREATE (:Fix {id:'fix-coupon-rounding', description:'Round percentage discounts correctly'})")
    db.query("CREATE (:Bug {id:'seed-tax-bug', description:'Tax is charged twice', created_at:'2026-10-09'})")
    db.query("CREATE (:Fix {id:'fix-tax-once', description:'Apply tax once after subtotal'})")
    db.query("CREATE (:Bug {id:'seed-cart-bug', description:'Removing an item does not update total', created_at:'2026-10-09'})")
    db.query("CREATE (:Fix {id:'fix-cart-update', description:'Recalculate total after removal'})")
    db.query(
        """
        MATCH (oldbug:Bug {id:'seed-coupon-bug'}), (oldfix:Fix {id:'fix-coupon-rounding'}),
        (coupon:Function {name:'applyCoupon'}), (c4:Commit {id:'fix901'}),
        (tc:Test {name:'coupon percentage regression test'}),
        (seedtax:Bug {id:'seed-tax-bug'}), (taxfix:Fix {id:'fix-tax-once'}),
        (tax:Function {name:'calculateTax'}), (c2:Commit {id:'def456'}),
        (tt:Test {name:'tax once regression test'}),
        (seedcart:Bug {id:'seed-cart-bug'}), (cartfix:Fix {id:'fix-cart-update'}),
        (remove:Function {name:'removeItem'}), (c3:Commit {id:'ghi789'}),
        (tr:Test {name:'cart removal regression test'})
        CREATE
        (oldbug)-[:AFFECTS]->(coupon), (oldbug)-[:RESOLVED_BY]->(oldfix),
        (oldfix)-[:IMPLEMENTED_BY]->(c4), (oldfix)-[:VERIFIED_BY]->(tc),
        (seedtax)-[:AFFECTS]->(tax), (seedtax)-[:RESOLVED_BY]->(taxfix),
        (taxfix)-[:IMPLEMENTED_BY]->(c2), (taxfix)-[:VERIFIED_BY]->(tt),
        (seedcart)-[:AFFECTS]->(remove), (seedcart)-[:RESOLVED_BY]->(cartfix),
        (cartfix)-[:IMPLEMENTED_BY]->(c3), (cartfix)-[:VERIFIED_BY]->(tr)
        """
    )
    print("Bug Trail graph seeded successfully.")


if __name__ == "__main__":
    main()
