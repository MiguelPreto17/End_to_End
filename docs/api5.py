# Make sure install: pip install requests

import requests
import re
from datetime import datetime
import pandas as pd
import json


def fetch_file_content(file_url):
    """Fetch and return the content of the file at the given URL."""
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching file content from {file_url}. Status code: {response.status_code}")
        return None


def fetch_files_recursive(api_url, token, user, repo):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching data from GitHub. Status code: {response.status_code}. Message: {response.text}")
        return []

    items = response.json()
    # print(f"Fetched items from: {api_url} -> {items}")  # Debug print

    if not items:
        print(f"No items found in: {api_url}")
        return []

    files = [item for item in items if item['type'] == 'file']
    dirs = [item for item in items if item['type'] == 'dir']

    for dir_item in dirs:
        dir_api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{dir_item['path']}?ref=master"
        print(f"Entering directory: {dir_item['path']} -> {dir_api_url}")
        files.extend(fetch_files_recursive(dir_api_url, token, user, repo))

    return files


def get_latest_forecast_file_url(repo_url, token):
    # Extract user and repo from the URL
    user, repo = repo_url.split("github.com/")[1].split("/")

    # Construct the API URL
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents?ref=master"
    files = fetch_files_recursive(api_url, token, user, repo)

    pattern = r"^Forecast Values (\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).txt$"
    latest_date = datetime.min
    latest_file_url = ""

    for file in files:
        name = file['name']
        print(f"Checking: {name}")
        match = re.search(pattern, name)

        if match:
            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            if date_obj > latest_date:
                latest_date = date_obj
                latest_file_url = file['download_url']

    if not latest_file_url:
        raise ValueError("No matching files found")

    # Fetch and print the content of the latest file
    content = fetch_file_content(latest_file_url)
    if content:
        print("\nContents of the latest forecast file:\n", content)

    return latest_file_url

def get_forecast_data(repo_url, token):
    # A função para obter os dados de previsão

    latest_file_url = get_latest_forecast_file_url(repo_url, token)
    content = fetch_file_content(latest_file_url)

    # Carregar o conteúdo JSON
    forecast_json = json.loads(content)
    forecast_items = forecast_json["forecast_data"]

    timestamps = []
    values = []

    for item in forecast_items:
        timestamp_str = item["timestamp"]
        value = item["value"]

        timestamps.append(timestamp_str)
        values.append(value)

    data = {'Datetime': timestamps, 'Value': values}
    df = pd.DataFrame(data)

    return df



repo_url = "https://github.com/Wakiloo7/hems-forecast-value"
token = "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"

forecast_data = get_forecast_data(repo_url, token)

# Salvar os dados em um arquivo Excel
excel_filename = "forecast_data.csv"
forecast_data.to_excel(excel_filename, index=False)
print(f"Dados de previsão salvos no arquivo: {excel_filename}")
print(get_latest_forecast_file_url(repo_url, token))