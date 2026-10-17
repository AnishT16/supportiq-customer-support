---
title: "[Backend] Customer, Product, Order, Payment & Delivery Models with Seed Data & REST APIs"
labels: ["backend", "database", "api", "dev-a", "milestone-2"]
assignee: "Dev A"
milestone: "Milestone 2: Core E-Commerce Entities"
dependencies: ["ISSUE-01", "ISSUE-03"]
---

## Summary & Objective
Implement core transactional business models as outlined in Section 12 of README.md: `Customer`, `Product`, `Order`, `OrderItem`, `Payment`, and `Delivery`. Provide REST endpoints for order listing, order details, and customer state lookup, backed by automated seed fixtures.

## Specifications & Requirements
- Models:
  - `Customer`: linked to User, `previous_complaints_count`, `previous_refunds_count`, `is_flagged`.
  - `Product`: `name`, `sku`, `price`, `category`, `stock_quantity`, `is_returnable`.
  - `Order`: `customer`, `status` (`ACTIVE`, `PAID`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`, `REFUNDED`), `total_amount`, `discount_amount`, `coupon_code`.
  - `OrderItem`: `order`, `product`, `quantity`, `unit_price`, `subtotal`.
  - `Payment`: `order`, `method` (`CREDIT_CARD`, `WALLET`, `STORE_CREDIT`), `status` (`PAID`, `REFUNDED`, `FAILED`), `transaction_id`.
  - `Delivery`: `order`, `tracking_number`, `carrier`, `shipping_tier` (`STANDARD`, `EXPEDITED`, `OVERNIGHT`), `delivery_status` (`NOT_SHIPPED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`), `estimated_delivery_date`, `delay_days`.
- Endpoints:
  - `GET /api/orders/` (Filtered by authenticated customer; agents/managers see all)
  - `GET /api/orders/{id}/` (Detailed order view including items, payment, and delivery status)
  - `GET /api/customers/{id}/` (Agent/Manager lookup of customer risk history)
- Management Command:
  - `python manage.py seed_ecommerce` to generate realistic demo orders and deliveries matching policy test cases.

## Sample Response Contract
`GET /api/orders/1001/`
```json
{
  "order_id": 1001,
  "customer_id": 901,
  "status": "ACTIVE",
  "total_amount": 750.0,
  "discount_amount": 0.0,
  "coupon_code": null,
  "items": [
    { "product_id": 5, "product_name": "Noise Cancelling Headphones", "quantity": 1, "unit_price": 750.0 }
  ],
  "payment": { "method": "CREDIT_CARD", "status": "PAID" },
  "delivery": {
    "tracking_number": "TRK9281928",
    "carrier": "FedEx",
    "status": "NOT_SHIPPED",
    "delay_days": 0
  }
}
```

## Acceptance Criteria
- [ ] Django models created and migrated cleanly.
- [ ] Customer users can only view their own orders; Agents and Managers can inspect all orders.
- [ ] `seed_ecommerce` management command populates representative orders (active, shipped, delayed, high-value).
- [ ] Automated tests verify permissions, relationships, and serialization accuracy.
