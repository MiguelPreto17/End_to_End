import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_values_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all rows in the table
    table_rows = soup.find_all('tr')

    # Extract data from each cell in the row
    values = []
    for row in table_rows:
        cells = row.find_all('td')
        row_data = [cell.text.strip() for cell in cells]
        values.append(row_data)

    return values

def extract_values_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Extract values from HTML content
        values = extract_values_from_html(response.text)
        print(values)
        if values:
            # Save the DataFrame to a CSV file
            df = pd.DataFrame(values,
                              columns=["Date", "Load"])  # Adicione os nomes das colunas conforme necessário
            df.to_csv('forecast_data.csv', sep=';', decimal=',', index=True)
            print('Arquivo CSV salvo com sucesso.')
        else:
            print('Erro na solicitação ou na extração dos dados.')
        #return values
    except requests.RequestException as e:
        print(f"Failed to fetch the content due to: {e}")
        return None



