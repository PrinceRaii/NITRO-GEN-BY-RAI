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

logging.basicConfig(level=logging.INFO, filename='nitro_link_generator.log', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def generate_gift_code(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_nitro_gift_link():
    code = generate_gift_code(16)
    return f"https://discord.gift/{code}"

def validate_nitro_link(link):
    try:
        response = requests.get(link, timeout=5)
        if response.status_code == 200 and "successfully claimed" in response.text:
            return True
        elif response.status_code == 404:
            return False
        else:
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error validating link {link}: {e}")
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

def hash_link(link):
    return hashlib.md5(link.encode()).hexdigest()

def print_summary(links):
    total_links = len(links)
    valid_links = sum(1 for _, valid in links if valid)
    invalid_links = total_links - valid_links
    logging.info(f"Summary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")
    print(f"\nSummary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")

def continuous_generation_and_validation():
    print("Continuous Nitro Gift Link Generation and Validation Started. Press Ctrl+C to stop.")
    while True:
        links = []
        with tqdm(total=100, desc="Generating Nitro Gift Links") as pbar:
            for _ in range(100):
                link = generate_nitro_gift_link()
                links.append((link, None))
                pbar.update(1)

        valid_links = []
        with tqdm(total=len(links), desc="Validating Nitro Gift Links") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(validate_nitro_link, link): link for link, _ in links}

                for future in concurrent.futures.as_completed(futures):
                    link = futures[future]
                    valid = future.result()
                    valid_links.append((link, valid))
                    pbar.update(1)

        save_valid_links(valid_links)
        export_to_csv(valid_links)
        export_to_json(valid_links)
        print_summary(valid_links)
        time.sleep(2)

def main():
    print("Welcome to the Nitro Gift Link Generator!")
    continuous_generation_and_validation()

if __name__ == "__main__":
    main()
