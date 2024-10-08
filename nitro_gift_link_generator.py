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

# Set up logging
logging.basicConfig(level=logging.INFO, filename='nitro_link_generator.log', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to generate a random alphanumeric code of fixed length
def generate_gift_code(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Generate Nitro gift link
def generate_nitro_gift_link():
    code = generate_gift_code(16)  # Fixed length of 16 characters
    return f"https://discord.gift/{code}"

# Validate the Nitro gift link by making an HTTP request
def validate_nitro_link(link):
    try:
        response = requests.get(link, timeout=5)  # Set a timeout for the request
        if response.status_code == 200 and "successfully claimed" in response.text:
            return True  # Link is valid and claimed successfully
        elif response.status_code == 404:
            return False  # Link does not exist
        else:
            return False  # Any other status is considered invalid
    except requests.exceptions.RequestException as e:
        logging.error(f"Error validating link {link}: {e}")
        return False  # In case of any request errors

# Export generated links to a CSV file
def export_to_csv(links):
    with open("generated_links.csv", "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Link", "Hashed Link", "Valid", "Timestamp"])
        for link, valid in links:
            hashed = hash_link(link)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([link, hashed, valid, timestamp])
    logging.info("Links exported to generated_links.csv.")

# Export generated links to a JSON file
def export_to_json(links):
    with open("generated_links.json", "w") as jsonfile:
        json_data = [{"link": link, "hashed": hash_link(link), "valid": valid, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for link, valid in links]
        json.dump(json_data, jsonfile)
    logging.info("Links exported to generated_links.json.")

# Save valid links to a text file
def save_valid_links(links):
    with open("valid_links.txt", "a") as validfile:  # Append mode
        for link, valid in links:
            if valid:
                validfile.write(f"{link}\n")
    logging.info("Valid links saved to valid_links.txt.")

# Function to hash the link using MD5
def hash_link(link):
    return hashlib.md5(link.encode()).hexdigest()

# Print summary statistics
def print_summary(links):
    total_links = len(links)
    valid_links = sum(1 for _, valid in links if valid)
    invalid_links = total_links - valid_links
    logging.info(f"Summary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")
    print(f"\nSummary: {total_links} links generated, {valid_links} valid links, {invalid_links} invalid links.")

# Continuous generation and validation of links
def continuous_generation_and_validation():
    print("Continuous Nitro Gift Link Generation and Validation Started. Press Ctrl+C to stop.")
    while True:
        # Generate links
        links = []
        with tqdm(total=100, desc="Generating Nitro Gift Links") as pbar:
            for _ in range(100):  # Generate 100 links at a time
                link = generate_nitro_gift_link()
                links.append((link, None))
                pbar.update(1)

        # Validate generated links in parallel
        valid_links = []
        with tqdm(total=len(links), desc="Validating Nitro Gift Links") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # Adjust number of threads
                futures = {executor.submit(validate_nitro_link, link): link for link, _ in links}

                for future in concurrent.futures.as_completed(futures):
                    link = futures[future]
                    valid = future.result()
                    valid_links.append((link, valid))
                    pbar.update(1)

        # Save valid links
        save_valid_links(valid_links)

        # Automatically export results to CSV and JSON
        export_to_csv(valid_links)
        export_to_json(valid_links)

        # Print summary of results
        print_summary(valid_links)

        # Wait for a short period before generating again
        time.sleep(2)  # Adjust the sleep time as needed

def main():
    print("Welcome to the Nitro Gift Link Generator!")

    # Start continuous generation and validation
    continuous_generation_and_validation()

if __name__ == "__main__":
    main()
