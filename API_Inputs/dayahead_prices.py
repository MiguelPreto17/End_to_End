import requests
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd


# URL da API da Entsoe Transparency para os preços de Day-Ahead em formato CSV
url = 'https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart=202308010000&periodEnd=202308300000'
#url = 'https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YCZ-CEPS-----N&out_Domain=10YCZ-CEPS-----N&periodStart=202201010000&periodEnd=202212312300'

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
        'DateTime': [],
        #'EndTime': [],
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
                data['DateTime'].append(current_time)
                #data['EndTime'].append(current_time + timedelta(hours=1))
                data['Price'].append(price)
                x += 1
                print(current_time, price)



    pd.DataFrame(data).to_csv('dayahead_prices.csv', sep=';', decimal=',', index=True)

    """# Salvar os dados em um arquivo CSV local
    with open('dayahead_prices.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['StartTime', 'Price'])
        writer.writerows(data)"""


    print('Arquivo CSV salvo com sucesso.')
else:
    # Lidar com erros de solicitação, se necessário
    print('Erro na solicitação:', response.status_code)




"""response = requests.get(url)

if response.status_code == 200:
    data = response.content.decode('utf-8')
    with open('day-ahead-prices.csv', 'w') as f:
        f.write(data)
else:
    print('Error: {}'.format(response.status_code))"""
