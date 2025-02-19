import requests
from bs4 import BeautifulSoup
import json
from time import sleep

def parse_page(url, page_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        # Set a timeout of 3 seconds
        response = requests.get(url, headers=headers, timeout=3)
        
        if response.status_code in [403, 404]:
            print(f"HTTP {response.status_code} for ID: {page_id}")
            return {"id": page_id, "error": f"HTTP {response.status_code}"}

        if response.status_code != 200:
            print(f"Unexpected HTTP {response.status_code} for ID: {page_id}")
            return {"id": page_id, "error": f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract data with safe handling
        def safe_find(selector, attr=None):
            element = soup.select_one(selector)
            return element[attr] if element and attr else element.text.strip() if element else None

        name = safe_find('meta[property="og:title"]', 'content')
        description = safe_find('meta[property="og:description"]', 'content')
        region = safe_find('div.field-label:-soup-contains("Регионы") + div.field-content')
        workplace = safe_find('div.field-item.workplace > div.field-content')
        position = safe_find('div.field-item.workplace-post > div.field-content')
        education = safe_find('div.field-item.education > div.field-content')
        election_type = safe_find('div.field-item.election-type > div.field-content')
        birthday = safe_find('div.field-item.birthday span.date-display-single')

        # Education institutions
        education_institutions = [
            item.text.strip() for item in soup.select('div.field-item.even, div.field-item.odd')
        ]

        about = safe_find('div.field-item.about > div.field-content')
        deputy_post = safe_find('div.field-item.deputy-post > div.field-content')

        # Clean fields to remove backslashes
        def clean_field(field):
            return field.replace("\\", "") if field else None

        return {
            "id": page_id,
            "name": name,
            "description": clean_field(description),
            "region": region,
            "workplace": workplace,
            "position": position,
            "education": education,
            "election_type": clean_field(election_type),
            "birthday": birthday,
            "education_institutions": education_institutions,
            "about": clean_field(about),
            "deputy_post": deputy_post,
        }

    except requests.exceptions.Timeout:
        print(f"Timeout for ID: {page_id}")
        return {"id": page_id, "error": "Timeout"}

    except Exception as e:
        print(f"Error parsing page ID {page_id}: {e}")
        return {"id": page_id, "error": str(e)}

def collect_data(base_url, id_range):
    all_data = []
    error_log = []

    for i, page_id in enumerate(id_range, 1):
        url = f"{base_url}{page_id}"
        print(f"Parsing page: {url}")
        data = parse_page(url, page_id)

        if "error" in data:
            error_log.append(data)
        else:
            all_data.append(data)

        # Save progress every 50,000 pages
        if i % 50000 == 0:
            print(f"Saving progress at ID {page_id}...")
            save_to_json(all_data, f'new_all_data_{page_id}.json')
            save_to_json(error_log, f'new_error_log_{page_id}.json')

        # Adjust delay to 0 seconds (if faster handling is required)
        sleep(0)

    return all_data, error_log

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Main process
base_url = "https://ideputat.er.ru/user/"
id_range = range(300000, 500000)  # Range of IDs from 300000 to 500000

data, error_log = collect_data(base_url, id_range)

# Save final results
if data:
    save_to_json(data, 'new_all_data_final.json')
    print(f"Data saved to new_all_data_final.json. Records collected: {len(data)}")

if error_log:
    save_to_json(error_log, 'new_error_log_final.json')
    print(f"Errors saved to new_error_log_final.json. Errors recorded: {len(error_log)}")
