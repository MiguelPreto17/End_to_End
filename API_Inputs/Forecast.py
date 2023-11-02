import requests
from bs4 import BeautifulSoup

URL = "http://10.61.6.197:8083/view/Forecast%20Values%202023-08-25_00-00-00Z.txt"

def extract_values_from_url(url):
    try:
        response = requests.get(url, timeout=10)  # adding a timeout for good measure
        response.raise_for_status()  # will raise an exception if the HTTP code is 4xx or 5xx

        # Since the file is plain text, we might not need BeautifulSoup, but I'll keep it for now
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('pre').text
        return content
    except requests.RequestException as e:  # catch any requests exceptions
        print(f"Failed to fetch the content due to: {e}")
        return None

if __name__ == "__main__":
    values = extract_values_from_url(URL)
    if values:
        print(values)

