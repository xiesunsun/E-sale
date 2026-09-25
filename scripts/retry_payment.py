import random
import time
import uuid
import httpx

ORDER_ID = 1
MAX_ATTEMPTS = 3
idempotency_key = str(uuid.uuid4())
headers = {
    "Idempotency-Key": idempotency_key,
}
for attempt in range(MAX_ATTEMPTS):
    try:
        response = httpx.post(
            f"http://127.0.0.1:9999/orders/{ORDER_ID}/pay",
            headers=headers,
            timeout=1.0,
        )
        if response.status_code == 200:
            print("success", response.json())
            break
        if response.status_code in {502, 503, 504}:
            print("temporay server error")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                delay = float(retry_after)
            else:
                dealay = min(0.5 * (2**attempt), 4.0)
                delay += random.uniform(0, 0.2)
            print("rate limited")
        else:
            print(
                "non-retryable error",
                response.status_code,
                response.text,
            )
            break
    except httpx.TimeoutException:
        print("timeout")
    except httpx.ConnectError:
        print("connection failed")
    if attempt < MAX_ATTEMPTS - 1:
        delay = min(0.5 * (2**attempt), 4.0)
        delay += random.uniform(0, 0.2)
        print(f"retry after {delay:.2f} seconds")
        time.sleep(delay)
