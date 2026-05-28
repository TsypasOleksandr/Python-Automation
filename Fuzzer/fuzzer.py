import requests
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

def check_directory(base_url, directory):
    """Checks a single directory with browser emulation."""

    url = urljoin(base_url, directory)

    # Simulate Chrome browser to avoid simple bot blocking
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            return (url, response.status_code, "FOUND")

        elif response.status_code == 403:
            return (url, response.status_code, "ACCESS DENIED")

        elif response.status_code == 404:
            return (url, response.status_code, "NOT FOUND")

        else:
            return (
                url,
                response.status_code,
                f"STATUS {response.status_code}"
            )

    except requests.Timeout:
        return (url, 0, "TIMEOUT")

    except Exception:
        return (url, 0, "CONNECTION ERROR")


def fuzz_directories(base_url, wordlist, num_threads=10):
    """Main fuzzing function."""

    print(f"\n[*] Starting fuzzing on {base_url}...")
    print(f"[*] Checking {len(wordlist)} entries using {num_threads} threads.\n")

    found = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:

        results = executor.map(
            lambda d: check_directory(base_url, d),
            wordlist
        )

        for url, status, message in results:

            if status == 200:
                print(f"[+] {url} ({status}) - {message}")
                found.append(url)

            elif status == 403:
                print(f"[!] {url} ({status}) - {message}")

    print("\n===================================")
    print("[✓] Scan completed")
    print(f"[✓] Accessible directories found: {len(found)}")
    print("===================================\n")

    # Separate list of accessible directories
    if found:
        print("[ACCESSIBLE DIRECTORIES]\n")

        for item in found:
            print(item)

    else:
        print("No accessible directories were found.")

    return found


if __name__ == "__main__":

    # 1. Target website
    target_site = "http://example.com"

    # 2. Path to wordlist file
    wordlist_file = "directory-list-2.3-small.txt"

    try:
        with open(wordlist_file, "r") as f:

            # Read lines and remove empty entries
            my_wordlist = [
                line.strip()
                for line in f
                if line.strip()
            ]

        fuzz_directories(
            target_site,
            wordlist=my_wordlist,
            num_threads=15
        )

    except FileNotFoundError:
        print(f"[-] Error: File '{wordlist_file}' not found!")
