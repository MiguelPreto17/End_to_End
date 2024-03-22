import datetime
from API_Inputs.dayahead_prices import extract_prices
from API_Inputs.emissions import extract_co2_forecast
from API_Inputs.Forecast import extract_values_from_url
from API_Inputs.Final_file import final_file

def parameters():

    # Escolha da Objective_Function
    Objective_Function = "Cost"
    Objective_Function2 = "b"



    # Data atual
    current_date_obj = datetime.datetime.now()

    # Datas para input precos
    initial_date = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    final_date = (current_date_obj + datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0).strftime( "%Y%m%d%H%M%S")
    # Mantendo apenas os últimos 4 dígitos na parte dos segundos
    initial_date = initial_date[:-2]  # Remover os últimos 4 dígitos
    final_date = final_date[:-2]  # Remover os últimos 4 dígitos
    url = f"https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart={initial_date}&periodEnd={final_date}"

    # Datas para input C02
    date = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
    values_url = f"http://10.61.6.197:8083/view/Forecast%20Values%{date}.txt"

    # Datas para input Load
    startdate = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    enddate = (current_date_obj + datetime.timedelta(days=1)).replace(hour=23, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(startdate, enddate)

    params = {
            'geo_id': '1',
            'keep_oldest_only': 'true',
            'remove_duplicates': 'true',
            'start_date': startdate,
            'end_date': enddate,
            'format': 'json',
        }

    extract_prices(url)
    extract_co2_forecast(params)
    extract_values_from_url(values_url)
    final_file(Objective_Function)
    final_file(Objective_Function2)
