# Payment Endpoint Design

## Goal

Add `POST /orders/{order_id}/pay` so an order can be paid exactly once, including
when two requests arrive concurrently.

## Behavior

- A `CREATED` order is changed to `PAID` and receives one payment record.
- A payment request for an unknown order returns `404`.
- A payment request for an order that is no longer `CREATED` returns `429`.
- A successful payment returns `200` with the updated order.

## Data and transaction

`init_db` will create a `payments` table with a unique `order_id` column. The
payment handler will use one SQLite transaction:

1. Read the order and return `404` if it does not exist.
2. Update the order from `CREATED` to `PAID`.
3. If no row was updated, return `429`.
4. Insert the payment row and commit.

The conditional update and unique constraint protect the invariant that only
one concurrent request can complete payment for an order. The existing
connection helper and environment-selected database path remain unchanged.

## Testing

Keep the existing order API test and make the payment concurrency test pass.
The payment test verifies that two concurrent requests produce one `200` and
one `429`, leave the order `PAID`, and create exactly one payment record.
