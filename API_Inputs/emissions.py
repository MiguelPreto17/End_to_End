#!/usr/bin/env python
# coding: utf-8

# In[26]:
import pandas as pd
import requests
import json

def extract_co2_forecast(params):

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': 'BB6djHqTH5pLjt9TJdroG2ZuEys5ccMlpAsmBCPeX7ta7ARC3baIAq2AX5fqjREl',
    }

    json_data = {
        'email': 'alexandre.lucas@inesctec.pt',
        'password': 'sd32!xxz64',
    }

    r = requests.post('http://vcpes08.inesctec.pt:8000/account/login/', headers=headers, json=json_data)

    # Creates Dictionary from json
    r_dict = r.json()
    # Prints token
    print('Access Token:', r_dict['token'])

    # Token format to pass to Sentinel
    token = {"Authorization": "Token {}".format(r_dict['token'])}
    print(token)

    headers = {
        'accept': 'application/json',
        'X-CSRFToken': 'COfbXtvhFLUt9cJKtw2TV6GmeVeviGsX3NUnWsrhXL6JwppgFdupmhi40EadITyu',
    }

    response = requests.get('http://vcpes08.inesctec.pt:8000/data/inesctec/forecast/co2-intensity/', params=params, headers=token)
    json_object = json.loads(response.content)
    json_to_str = json.dumps(json_object, indent=2)

    print(json_to_str)

    # Convert the API response content to a JSON object
    response_json = response.json()

    # Access the correct JSON data (assuming it's in 'data' field)
    data_list = response_json['data']

    # Extract datetime and value from the JSON data and create a dictionary
    data = {
        'Datetime': [item['datetime'] for item in data_list],
        'Value': [item['value'] for item in data_list]
    }

    # Create a DataFrame from the dictionary
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file
    df.to_csv('output_data.csv', sep=';', decimal=',', index=True)

    if response.status_code == 200:

        print('Arquivo CSV salvo com sucesso.')
    else:
        # Lidar com erros de solicitação, se necessário
        print('Erro na solicitação:', response.status_code)

