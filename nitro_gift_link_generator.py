import random
import string
import concurrent.futures
import csv
import json
import hashlib
import datetime
import logging
import requests
from tqdm import tqdm
import time

# Initialize logging with error and info levels
logging.basicConfig(
    level=logging.INFO, 
    filename='nitro_link_generator.log', 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Startup message with ASCII art and creator name
startup_message = r"""
|\   __  \|\   __  \|\  \|\   ___  \|\   ____\|\  ___ \
\ \  \|\  \ \  \|\  \ \  \ \  \\ \  \ \  \___|\ \   __/|
 \ \   ____\ \   _  _\ \  \ \  \\ \  \ \  \    \ \  \_|/__
  \ \  \___|\ \  \\  \\ \  \ \  \\ \  \ \  \____\ \  \_|\ \
   \ \__\    \ \__\\ _\\ \__\ \__\\ \__\ \_______\ \_______\
    \|__|     \|__|\|__|\|__|\|__| \|__|\|_______|\|_______|



 ________  ________  ___  ___
|\   __  \|\   __  \|\  \|\  \
\ \  \|\  \ \  \|\  \ \  \ \  \
 \ \   _  _\ \   __  \ \  \ \  \
  \ \  \\  \\ \  \ \  \ \  \ \  \
   \ \__\\ _\\ \__\ \__\ \__\ \__\
    \|__|\|__|\|__|\|__|\|__|\|__|    

Created by Prince Raii
"""
print(startup_message)

def generate_gift_code(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_nitro_gift_link():
    code = generate_gift_code(16)
    return f"https://discord.gift/{code}"

def validate_nitro_link(link, proxy=None, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            response = requests.get(link, proxies=proxies, timeout=5)
            
            if response.status_code == 200 and "successfully claimed" in response.text:
                logging.info(f"Link validated: {link} - Claimed")
                return True
            elif response.status_code == 404:
                logging.info(f"Link validated: {link} - Not valid")
                return False
            else:
                logging.info(f"Link validated: {link} - Unknown status")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error validating link {link} with proxy {proxy}: {e}")
            attempt += 1
            time.sleep(1)
    return False

def export_to_csv(links):
    with open("generated_links.csv", "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Link", "Hashed Link", "Valid", "Timestamp"])
        for link, valid in links:
            hashed = hash_link(link)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([link, hashed, valid, timestamp])
    logging.info("Links exported to generated_links.csv.")

def export_to_json(links):
    with open("generated_links.json", "w") as jsonfile:
        json_data = [{"link": link, "hashed": hash_link(link), "valid": valid, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for link, valid in links]
        json.dump(json_data, jsonfile)
    logging.info("Links exported to generated_links.json.")

def save_valid_links(links):
    with open("valid_links.txt", "a") as validfile:
        for link, valid in links:
            if valid:
                validfile.write(f"{link}\n")
    logging.info("Valid links saved to valid_links.txt.")

def export_statistics(links):
    total_links = len(links)
    valid_links = sum(1 for _, valid in links if valid)
    invalid_links = total_links - valid_links
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("link_statistics.txt", "a") as statsfile:
        statsfile.write(f"Statistics as of {timestamp}:\n")
        statsfile.write(f"Total Links Generated: {total_links}\n")
        statsfile.write(f"Valid Links: {valid_links}\n")
        statsfile.write(f"Invalid Links: {invalid_links}\n\n")
    
    logging.info("Statistics exported to link_statistics.txt.")

def hash_link(link):
    return hashlib.md5(link.encode()).hexdigest()

def print_summary(links):
    total_links = len(links)
    valid_links = sum(1 for _, valid in links if valid)
    invalid_links = total_links - valid_links
    logging.info(f"Summary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")
    print(f"\nSummary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")

def load_proxies(filename="proxies.txt"):
    with open(filename, "r") as file:
        return [line.strip() for line in file]

def continuous_generation_and_validation(use_proxies=False, num_links=100, cycle_timeout=2):
    print("Continuous Nitro Gift Link Generation and Validation Started. Press Ctrl+C to stop.")
    
    proxies = load_proxies() if use_proxies else []
    proxy_index = 0
    
    while True:
        links = []
        with tqdm(total=num_links, desc="Generating Nitro Gift Links") as pbar:
            for _ in range(num_links):
                link = generate_nitro_gift_link()
                links.append((link, None))
                pbar.update(1)

        valid_links = []
        with tqdm(total=len(links), desc="Validating Nitro Gift Links") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {}
                
                for link, _ in links:
                    proxy = proxies[proxy_index] if use_proxies and proxies else None
                    futures[executor.submit(validate_nitro_link, link, proxy)] = link
                    
                    proxy_index = (proxy_index + 1) % len(proxies) if proxies else 0

                for future in concurrent.futures.as_completed(futures):
                    link = futures[future]
                    valid = future.result()
                    valid_links.append((link, valid))
                    pbar.update(1)

        save_valid_links(valid_links)
        export_to_csv(valid_links)
        export_to_json(valid_links)
        export_statistics(valid_links)
        print_summary(valid_links)
        
        time.sleep(cycle_timeout)

def main():
    print("Welcome to the Nitro Gift Link Generator!")
    use_proxies = input("Do you want to use proxies? (yes/no): ").strip().lower() == "yes"
    if use_proxies:
        logging.info("Proxies enabled for validation.")
    else:
        logging.info("Proxies not enabled.")
        
    continuous_generation_and_validation(use_proxies, num_links=100, cycle_timeout=2)

if __name__ == "__main__":
    main()
