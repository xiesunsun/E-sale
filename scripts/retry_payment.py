import random
import time
import uuid
import httpx
ORDER_ID=1
MAX_ATTEMPTS=3
idempotency_key=str(uuid.uuid4())
headers={
    "Idempotency-Key": idempotency_key,   
}
for attempt in range(MAX_ATTEMPTS):
    try:
        response=httpx.post(
            f"http://127.0.0.1:8000/orders/{ORDER_ID}/pay",
            headers=headers,
            timeout=1.0,            
        )
        if response.status_code==200:
            print("success",response.json())
            break
        if response.status_code in {502,503,504}:
            print("temporay server error")
        else:
            print(
                "non-retryable error",
                response.status_code,
                response.text,
            )
    except httpx.TimeoutException:
        print("timeout")
    if attempt<MAX_ATTEMPTS-1:
        delay=min(0.5*(2**attempt),4.0)
        delay+=random.uniform(0,0.2)
        print(f"retry after {delay:.2f} seconds")
        time.sleep(delay)
        
