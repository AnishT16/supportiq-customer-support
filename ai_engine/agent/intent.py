"""
Intent Recognition & Entity Extraction for SupportIQ AI Support Agent.
Identifies customer intent and extracts operational entities (e.g. order IDs, amounts, reasons).
"""

import re
from typing import Any, Dict, List, Tuple
from ai_engine.agent.schemas import IntentType


# Ambiguous or generic phrases that lack sufficient intent
AMBIGUOUS_PATTERNS = [
    r"^\s*$",
    r"^\s*(?:hi|hello|hey|yo|greetings|hola)\s*[\.!?]*$",
    r"^\s*(?:help|support|agent|assist|assistance|someone)\s*[\.!?]*$",
    r"^\s*(?:what|why|how|who|can you help)\s*[\.!?]*$",
    r"^\s*[\?\!\.\s]+\s*$",
]

# Keyword and pattern rules for intent mapping
INTENT_RULES: List[Tuple[IntentType, List[str], float]] = [
    (
        IntentType.ORDER_CANCELLATION,
        [
            r"\bcancel\b",
            r"\bcancellation\b",
            r"\bstop\s+shipment\b",
            r"\bvoid\s+order\b",
            r"\bdrop\s+order\b",
            r"\bdo\s+not\s+ship\b",
        ],
        0.95,
    ),
    (
        IntentType.REFUND_REQUEST,
        [
            r"\brefund\b",
            r"\breturn\b",
            r"\bmoney\s+back\b",
            r"\breimburse\b",
            r"\bcredit\s+back\b",
            r"\breturn\s+window\b",
            r"\bdefective\s+item\b",
        ],
        0.92,
    ),
    (
        IntentType.EXPEDITE_SHIPPING,
        [
            r"\bexpedite\b",
            r"\brush\s+shipping\b",
            r"\bovernight\b",
            r"\bfaster\s+delivery\b",
            r"\bpriority\s+shipping\b",
        ],
        0.93,
    ),
    (
        IntentType.DELIVERY_TRACKING,
        [
            r"\bwhere\s+is\s+my\s+(?:order|package|item)\b",
            r"\btrack(?:ing)?\b",
            r"\bshipment\s+status\b",
            r"\bdelivery\s+(?:status|delay|delayed|time)\b",
            r"\bcourier\b",
            r"\bpackage\b",
            r"\bestimated\s+delivery\b",
        ],
        0.90,
    ),
    (
        IntentType.WARRANTY_INQUIRY,
        [
            r"\bwarranty\b",
            r"\bcare\+\b",
            r"\bcoverage\b",
            r"\bbroken\s+screen\b",
            r"\brma\b",
            r"\brepair\b",
            r"\bmanufacturer\s+warranty\b",
        ],
        0.90,
    ),
    (
        IntentType.PAYMENT_INQUIRY,
        [
            r"\bpayment\b",
            r"\bcredit\s+card\b",
            r"\bcoupon\b",
            r"\bchargeback\b",
            r"\bbilling\b",
            r"\bcharged\s+twice\b",
            r"\bpayment\s+method\b",
        ],
        0.88,
    ),
    (
        IntentType.POLICY_INQUIRY,
        [
            r"\bpolicy\b",
            r"\brules\b",
            r"\bterms\b",
            r"\bguidelines\b",
            r"\bfaq\b",
            r"\bhow\s+(?:long|does\s+it\s+take|many\s+days)\b",
        ],
        0.80,
    ),
]


class IntentClassifier:
    """
    Rule-based and pattern matching intent classifier with entity extraction.
    Provides fallback-safe intent detection with confidence scoring.
    """

    @classmethod
    def is_ambiguous(cls, message: str) -> bool:
        """Check if message is empty, whitespace, or generic greeting."""
        if not message or not message.strip():
            return True
        clean = message.strip().lower()
        if len(clean) < 3:
            return True
        for pattern in AMBIGUOUS_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                return True
        return False

    @classmethod
    def classify(cls, message: str) -> Tuple[IntentType, float]:
        """
        Classifies user intent from natural language message.

        Returns:
            Tuple of (IntentType, confidence_score)
        """
        if cls.is_ambiguous(message):
            return IntentType.AMBIGUOUS, 0.20

        clean = message.lower()

        # Score matching intents
        best_intent = IntentType.GENERAL_SUPPORT
        best_confidence = 0.50

        for intent_type, patterns, confidence in INTENT_RULES:
            for pattern in patterns:
                if re.search(pattern, clean, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
                    break

        return best_intent, best_confidence

    @classmethod
    def extract_entities(cls, message: str) -> Dict[str, Any]:
        """
        Extracts operational entities (order IDs, dollar amounts, keywords)
        from message.
        """
        entities: Dict[str, Any] = {}

        if not message:
            return entities

        # 1. Order ID matching: 'order 1001', 'order #10291', '#9281'
        order_match = re.search(
            r"(?:order|order\s*#|#)\s*([0-9]{3,7})\b", message, re.IGNORECASE
        )
        if order_match:
            try:
                entities["order_id"] = int(order_match.group(1))
            except ValueError:
                entities["order_id"] = order_match.group(1)

        # 2. Dollar amount matching: '$2499', '$2,499.00', '750 dollars'
        amount_match = re.search(
            r"(?:\$|usd\s*)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*(?:dollars|bucks)",
            message,
            re.IGNORECASE,
        )
        if amount_match:
            raw_amt = amount_match.group(1) or amount_match.group(2)
            try:
                entities["amount"] = float(raw_amt.replace(",", ""))
            except (ValueError, AttributeError):
                pass

        # 3. Defect or reason keywords
        reasons = []
        if re.search(r"\bdefective\b|\bfaulty\b|\bbroken\b", message, re.IGNORECASE):
            reasons.append("defective_product")
        if re.search(r"\bdelayed\b|\blate\b|\bnot\s+arrived\b", message, re.IGNORECASE):
            reasons.append("delivery_delay")
        if re.search(r"\bwrong\s+item\b|\bwrong\s+size\b", message, re.IGNORECASE):
            reasons.append("incorrect_item")
        if re.search(r"\bchanged\s+mind\b", message, re.IGNORECASE):
            reasons.append("buyer_remorse")

        if reasons:
            entities["reasons"] = reasons

        return entities
