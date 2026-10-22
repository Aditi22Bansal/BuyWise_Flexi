import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..models.data import Vendor, Quote, QuoteItem, QuoteStatus


@dataclass
class SimulatedVendorResponse:
    quote: Quote
    accepted_negotiation: bool
    counter_offer_note: str
    response_delay_seconds: float = 0.5


class SimulatedVendorChannel:
    """Simulated vendor negotiation channel (API / email / portal).

    In production this would be replaced with real vendor API clients
    (REST, SOAP, EDI, or email/SMTP integration).
    """

    def __init__(self, seed: Optional[int] = None, base_delay: float = 0.5):
        self.rng = random.Random(seed)
        self.base_delay = base_delay
        self._vendors: Dict[str, Vendor] = {}
        self._quote_counter = 0

    def register_vendor(self, vendor: Vendor):
        self._vendors[vendor.id] = vendor

    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        return self._vendors.get(vendor_id)

    def request_quote(self, vendor: Vendor, requirement, products) -> Quote:
        """Simulate a vendor submitting an initial quotation."""
        self._quote_counter += 1
        quote_id = f"Q-{vendor.id}-{self._quote_counter}"

        items = []
        total = 0.0
        for product in products:
            # Vendor marks up base price by a vendor-specific factor
            markup = self.rng.uniform(0.05, 0.25)
            unit_price = round(product.base_price * (1 + markup), 2)
            total_price = round(unit_price * requirement.quantity, 2)
            delivery_days = self.rng.randint(
                max(1, vendor.average_delivery_days - 3),
                vendor.average_delivery_days + 5,
            )
            warranty = max(requirement.warranty_months,
                           self.rng.randint(12, 36))
            items.append(QuoteItem(
                product_id=product.id,
                product_name=product.name,
                quantity=requirement.quantity,
                unit_price=unit_price,
                total_price=total_price,
                warranty_months=warranty,
                delivery_days=delivery_days,
                notes=f"Quoted by {vendor.name}",
            ))
            total += total_price

        # Apply volume discount if quantity is high
        discount = 0.0
        if requirement.quantity >= 10:
            discount = round(self.rng.uniform(0.02, 0.05), 2)
        total = round(total * (1 - discount), 2)

        valid_until = (datetime.utcnow() + timedelta(days=14)).isoformat()

        quote = Quote(
            id=quote_id,
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            items=items,
            total_amount=total,
            status=QuoteStatus.SUBMITTED,
            valid_until=valid_until,
            terms=vendor.payment_terms,
            discount_percent=discount,
            negotiation_round=0,
        )
        return quote

    def negotiate(self, vendor: Vendor, current_quote: Quote,
                  target_discount: float, round_number: int) -> SimulatedVendorResponse:
        """Simulate a negotiation round with the vendor.

        The vendor may counter with a higher discount, hold, or walk away.
        """
        time.sleep(self.base_delay)

        willingness = vendor.reliability_score  # more reliable vendors negotiate more
        concession_chance = 0.6 + (willingness * 0.3)

        accepted = False
        counter_note = "No further discount available."
        new_quote = None

        roll = self.rng.random()
        if roll < concession_chance and round_number <= 3:
            # Vendor concedes additional discount
            extra_discount = round(self.rng.uniform(0.01, target_discount), 2)
            total_discount = round(current_quote.discount_percent + extra_discount, 2)
            total_discount = min(total_discount, 0.25)  # cap at 25%

            new_total = round(current_quote.total_amount *
                              (1 - (total_discount - current_quote.discount_percent)), 2)
            new_quote = Quote(
                id=f"{current_quote.id}-R{round_number}",
                vendor_id=vendor.id,
                vendor_name=vendor.name,
                items=current_quote.items,
                total_amount=new_total,
                status=QuoteStatus.NEGOTIATED,
                valid_until=current_quote.valid_until,
                terms=current_quote.terms,
                discount_percent=total_discount,
                negotiation_round=round_number,
                metadata={"parent_quote_id": current_quote.id},
            )
            accepted = True
            counter_note = (f"Counter-offer: additional {extra_discount*100:.1f}% "
                            f"discount applied (total {total_discount*100:.1f}%).")
        elif roll < concession_chance + 0.15:
            # Vendor holds price
            counter_note = "Best and final offer. No further discount possible."
        else:
            # Vendor walks away on this round but may return
            counter_note = ("Unable to meet requested terms at this time. "
                            "Please contact for future opportunities.")

        return SimulatedVendorResponse(
            quote=new_quote if new_quote else current_quote,
            accepted_negotiation=accepted,
            counter_offer_note=counter_note,
            response_delay_seconds=self.base_delay,
        )

    def confirm_order(self, vendor: Vendor, quote: Quote) -> Dict[str, Any]:
        """Simulate confirming/placing an order with a vendor."""
        return {
            "order_id": f"ORD-{vendor.id}-{quote.id}",
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "quote_id": quote.id,
            "total_amount": quote.total_amount,
            "status": "confirmed",
            "confirmed_at": datetime.utcnow().isoformat(),
            "estimated_delivery_days": max(it.delivery_days for it in quote.items)
                                       if quote.items else 7,
        }