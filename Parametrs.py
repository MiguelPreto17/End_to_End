import datetime
from API_Inputs.dayahead_prices import extract_prices
from API_Inputs.emissions import extract_co2_forecast
from API_Inputs.Forecast import extract_values_from_url
from API_Inputs.Final_file import final_file



def parameters():

    Objective_Function = "Cost"

    current_date_obj = datetime.datetime.now()
    current_date5 = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
    values_url = f"http://10.61.6.197:8083/view/Forecast%20Values%{current_date5}.txt"


    current_date2 = current_date_obj.replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    current_date21 = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    current_date212 = (current_date_obj + datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
    # Mantendo apenas os últimos 4 dígitos na parte dos segundos
    current_date212 = current_date212[:-2]  # Remover os últimos 4 dígitos
    url = f"https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart={current_date21}&periodEnd={current_date212}"


    current_date3 = current_date_obj.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    current_date31 = (current_date_obj + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
            'geo_id': '1',
            'keep_oldest_only': 'true',
            'remove_duplicates': 'true',
            'start_date': current_date3,
            'end_date': current_date31,
            'format': 'json',
        }

    extract_prices(url)
    extract_co2_forecast(params)
    extract_values_from_url(values_url)
    final_file(Objective_Function)