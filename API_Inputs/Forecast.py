import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta


"""#url = "http://10.61.6.197:8083/view/Forecast%20Values%202023-11-30_00-00-00Z.txt"
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S%Z")
current_date2 = current_date.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d-%H-%M-%SZ")
values_url = f"http://10.61.6.197:8083/view/Forecast%20Values_{current_date2}.txt"
print(current_date)
print(current_date2)"""

#current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S%Z")
current_date_obj = datetime.now()
current_date2 = current_date_obj.replace(hour=0, minute=0, second=0, microsecond=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
current_date21 = (current_date_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
values_url = f"http://10.61.6.197:8083/view/Forecast%20Values%{current_date21}.txt"

#print(current_date)
print(current_date21)
print(values_url)

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


extract_values_from_url(values_url)

