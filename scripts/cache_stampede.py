from concurrent.futures import ThreadPoolExecutor

import httpx

URL = "http://127.0.0.1:8000/orders/1"


def get_order():
    response = httpx.get(URL)
    return response.status_code


with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(get_order) for _ in range(20)]

    results = [future.result() for future in futures]

print(results)
