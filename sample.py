import requests

BASE_URL = "http://localhost:8000"

embed_endpoint = f"{BASE_URL}/embed/text-to-text-uh"
reveal_endpoint = f"{BASE_URL}/recover/text-to-text-uh"

cover_text = "Alice opened a cold can of Pepsi while playing her piano"
secret = "Hi"

# ---------- 1. EMBED SECRET ----------
print("[*] Sending embed request...")
embed_payload = {
    "cover": cover_text,
    "secret": secret
}
embed_response = requests.post(embed_endpoint, json=embed_payload)

if embed_response.status_code == 200:
    embed_data = embed_response.json()
    if "stego_text" in embed_data:
        stego_text = embed_data["stego_text"]
        print("[+] Embed successful!")
        print("Stego Text:", stego_text)
    else:
        print("[!] Embed failed:", embed_data.get("error"))
        exit(1)
else:
    print("[!] Embed request failed with status", embed_response.status_code)
    exit(1)

# ---------- 2. REVEAL SECRET ----------
print("\n[*] Sending reveal request...")
reveal_payload = {
    "embedded": stego_text
}
reveal_response = requests.post(reveal_endpoint, json=reveal_payload)

if reveal_response.status_code == 200:
    reveal_data = reveal_response.json()
    recovered_secret = reveal_data.get("recovered_secret")
    print("[+] Reveal successful!")
    print("Recovered Secret:", recovered_secret)
else:
    print("[!] Reveal request failed with status", reveal_response.status_code)
