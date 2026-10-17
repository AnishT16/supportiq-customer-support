"""
Synthetic Operational Dataset Generator for Training Predictive Models.
Generates realistic e-commerce and customer-support event patterns.
"""

import numpy as np
import pandas as pd


def generate_synthetic_support_data(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic dataset simulating customer orders,
    logistical conditions, historical interactions, and support ticket occurrences.
    """
    rng = np.random.default_rng(random_state)

    customer_ids = rng.integers(1000, 9999, size=n_samples)
    delivery_delays = np.clip(rng.exponential(scale=1.2, size=n_samples), 0, 10).round(1)
    previous_complaints = rng.poisson(lam=0.8, size=n_samples)
    courier_reliability = np.clip(rng.normal(loc=0.85, scale=0.15, size=n_samples), 0.35, 1.0).round(2)
    warehouse_backlog = rng.choice(["Low", "Medium", "High"], size=n_samples, p=[0.6, 0.25, 0.15])
    order_values = np.clip(rng.lognormal(mean=4.8, sigma=1.1, size=n_samples), 15.0, 6000.0).round(2)
    payment_statuses = rng.choice(["PAID", "PENDING", "FAILED"], size=n_samples, p=[0.88, 0.08, 0.04])
    product_categories = rng.choice(
        ["Electronics", "Apparel", "Home", "Books", "Beauty"],
        size=n_samples,
        p=[0.35, 0.25, 0.15, 0.15, 0.10],
    )
    cancellation_history = rng.poisson(lam=0.5, size=n_samples)

    # Compute probability of raising a support ticket based on domain rules
    contact_probs = []
    issue_categories = []

    for i in range(n_samples):
        delay = delivery_delays[i]
        complaints = previous_complaints[i]
        courier = courier_reliability[i]
        backlog = warehouse_backlog[i]
        pay_status = payment_statuses[i]
        order_val = order_values[i]
        cancels = cancellation_history[i]
        category = product_categories[i]

        # Base risk log-odds
        risk_score = -2.2

        if delay > 2.0:
            risk_score += 1.2 * (delay - 1.5)
        if courier < 0.75:
            risk_score += 1.5 * (0.8 - courier)
        if backlog == "High":
            risk_score += 1.1
        elif backlog == "Medium":
            risk_score += 0.4
        if complaints > 0:
            risk_score += 0.8 * complaints
        if pay_status == "FAILED":
            risk_score += 2.5
        elif pay_status == "PENDING":
            risk_score += 1.2
        if order_val > 1500:
            risk_score += 0.5
        if cancels > 1:
            risk_score += 0.4 * cancels

        prob = 1.0 / (1.0 + np.exp(-risk_score))
        contact_probs.append(prob)

        # Decide if support is contacted
        contacted = rng.random() < prob

        # Determine likely issue category if contacted
        if contacted:
            if pay_status in ["FAILED", "PENDING"] and rng.random() < 0.8:
                issue = "payment_issue"
            elif delay > 2.0 and courier < 0.8:
                issue = "delivery_delay"
            elif order_val > 2000 and rng.random() < 0.4:
                issue = "refund_request"
            elif cancels > 0 and rng.random() < 0.4:
                issue = "cancellation"
            elif category == "Electronics" and rng.random() < 0.3:
                issue = "damaged_product"
            else:
                issue = rng.choice(
                    ["delivery_delay", "refund_request", "payment_issue", "cancellation", "damaged_product", "account"],
                    p=[0.40, 0.20, 0.15, 0.10, 0.10, 0.05],
                )
        else:
            issue = "none"

        issue_categories.append(issue)

    df = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "delivery_delay": delivery_delays,
            "previous_complaints": previous_complaints,
            "courier_reliability": courier_reliability,
            "warehouse_backlog": warehouse_backlog,
            "order_value": order_values,
            "payment_status": payment_statuses,
            "product_category": product_categories,
            "cancellation_history": cancellation_history,
            "contact_support": [1 if cat != "none" else 0 for cat in issue_categories],
            "issue_category": issue_categories,
        }
    )

    return df


if __name__ == "__main__":
    df = generate_synthetic_support_data(10)
    print("Generated 10 sample records:")
    print(df.head())
