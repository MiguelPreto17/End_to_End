import requests
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd

url2 = 'https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart=202308010000&periodEnd=202308300000'

current_date_obj = datetime.now()
#current_date2 = current_date_obj.replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
current_date2 = (current_date_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
current_date21 = (current_date_obj + timedelta(days=1)).replace(hour=23, minute=0, second=0).strftime("%Y%m%d%H%M%S")

# Mantendo apenas os últimos 4 dígitos na parte dos segundos
current_date2 = current_date2[:-2]  # Remover os últimos 4 dígitos
current_date21 = current_date21[:-2]  # Remover os últimos 4 dígitos
url = f"https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart={current_date2}&periodEnd={current_date21}"

print(current_date2)
print(url)
print(url2)

def extract_prices(url):

    # Realizar a solicitação GET
    response = requests.get(url)
    x = 0

    # Verificar se a solicitação foi bem-sucedida (código de status 200 indica sucesso)
    if response.status_code == 200:
       # Parsear o XML
        root = ET.fromstring(response.content)
        """print(response.content)"""

      #Extrair os dados relevantes do XML
        data = {
            'date': [],
            #'EndTime': [],
            'Price': []
        }

        #base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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

extract_prices(url)