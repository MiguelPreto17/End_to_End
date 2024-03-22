import requests
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd

def extract_prices(url):

    # Realizar a solicitação GET
    response = requests.get(url)
    x = 0

    # Verificar se a solicitação foi bem-sucedida (código de status 200 indica sucesso)
    if response.status_code == 200:
       # Parsear o XML
        root = ET.fromstring(response.content)

      #Extrair os dados relevantes do XML
        data = {
            'date': [],
            'Price': []
        }

        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        current_time = base_date
        x = 0
        for series in root.findall('.//{*}TimeSeries'):
            for point in series.findall('.//{*}Period'):
                start_time_str = point.find('.//{*}timeInterval/{*}start').text
                #end_time_str = point.find('.//{*}timeInterval/{*}end').text
                #price = point.find('.//{*}price/{*}amount').NoneType
                for position in series.findall('.//{*}Point'):
                    price = position.find('.//{*}price.amount').text
                    #data.append([start_time, end_time, price])
                    start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%MZ")
                    #end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%MZ")
                    # Adicionar a hora atual aos dados
                    current_time = start_time + timedelta(hours=x)
                    #data.append([current_time, current_time + timedelta(hours=1), price])
                    data['date'].append(current_time)
                    #data['EndTime'].append(current_time + timedelta(hours=1))
                    data['Price'].append(price)
                    x += 1
                    print(current_time, price)

        pd.DataFrame(data).to_csv('dayahead_prices.csv', sep=';', decimal=',', index=True)
        print('Arquivo CSV salvo com sucesso.')
    else:
        # Lidar com erros de solicitação, se necessário
        print('Erro na solicitação:', response.status_code)

