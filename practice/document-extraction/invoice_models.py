# pip install python-dateutil

from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional
from dateutil import parser as dateparser
from enum import Enum

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float

class Invoice(BaseModel):
    vendor_name: str
    invoice_number: Optional[str] = None
    invoice_date: str
    line_items: List[LineItem]
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    total_amount: float


class PaymentTerms(str, Enum):
    net_15 = "NET_15"
    net_30 = "NET_30"
    net_60 = "NET_60"
    due_on_receipt = "DUE_ON_RECEIPT"
    
    @model_validator(mode="after")
    def check_totals_add_up(self):
        line_sum = sum(item.line_total for item in self.line_items)
        if abs(line_sum - self.subtotal) > 0.01:
            raise ValueError(f"Line items sum to {line_sum}, but subtotal is {self.subtotal}")

        discount = self.discount or 0
        expected_total = self.subtotal - discount + self.tax
        if abs(expected_total - self.total_amount) > 0.01:
            raise ValueError(f"Expected total {expected_total:.2f}, but got {self.total_amount}")

        return self


    @field_validator("invoice_date")
    @classmethod
    def normalize_date(cls, v: str) -> str:
        try:
            parsed = dateparser.parse(v)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            raise ValueError(f"Could not parse date: '{v}'")
        
    @field_validator("subtotal", "discount", "tax", "total_amount", mode="before")
    @classmethod
    def parse_currency(cls, v):
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").replace("-", "").strip()
            return float(cleaned)
        return v
    
    @field_validator("payment_terms", mode="before")
    @classmethod
    def normalize_terms(cls, v: str) -> str:
        v_lower = v.lower()
        if "30" in v_lower: return "NET_30"
        if "15" in v_lower: return "NET_15"
        if "60" in v_lower: return "NET_60"
        if "receipt" in v_lower: return "DUE_ON_RECEIPT"
        raise ValueError(f"Could not normalize payment terms: '{v}'")   