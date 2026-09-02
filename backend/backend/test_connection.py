import httpx

try:
    url = "https://nlhpwawrnmecnrwrgdvn.supabase.co"
    print(f"Testing connection to: {url}")
    response = httpx.get(url, timeout=10.0)
    print("Success! Status code:", response.status_code)
except Exception as e:
    print("Error occurred:")
    print(e)