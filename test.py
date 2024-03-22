import unittest
from datetime import datetime, timedelta
from API_Inputs.dayahead_prices import extract_prices
from API_Inputs.emissions import extract_co2_forecast
from API_Inputs.Forecast import extract_values_from_url
from API_Inputs.Final_file import final_file
from Parametrs import parameters
from database import upload_latest_file
from main import optimize


class TestParameters(unittest.TestCase):

    # Adicione métodos de teste para cada função
    """ def test_extract_prices_success(self):
        # Substitua a URL com um URL válido para seus testes
        current_date_obj = datetime.now()
        current_date21 = (current_date_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime( "%Y%m%d%H%M%S")
        current_date212 = (current_date_obj + timedelta(days=2)).replace(hour=0, minute=0, second=0).strftime( "%Y%m%d%H%M%S")
        # Mantendo apenas os últimos 4 dígitos na parte dos segundos
        current_date212 = current_date212[:-2]  # Remover os últimos 4 dígitos
        url = f"https://web-api.tp.entsoe.eu/api?securityToken=efb2ca19-add3-42d4-84e6-8e83986591e3&documentType=A44&in_Domain=10YPT-REN------W&out_Domain=10YPT-REN------W&periodStart={current_date21}&periodEnd={current_date212}"

        # Chame a função extract_prices com a URL de teste
        extract_prices(url)

        # Adapte isso conforme necessário para verificar os resultados esperados
        # Aqui, estamos apenas verificando se o arquivo CSV foi criado
        # e se contém pelo menos uma linha
        with open('dayahead_prices.csv', 'r') as file:
            content = file.read()
            self.assertTrue(content.strip())  # Verifica se o arquivo não está vazio


    def test_extract_co2_forecast_success(self):
        # Escreva um teste para o caso de sucesso da função extract_co2_forecast
        params = {
            'geo_id': '1',
            'keep_oldest_only': 'true',
            'remove_duplicates': 'true',
            'start_date': '2022-03-01T00:00:00Z',
            'end_date': '2022-03-02T00:00:00Z',
            'format': 'json',
        }

        # Chame a função extract_co2_forecast com os parâmetros de teste
        extract_co2_forecast(params)

        # Adapte isso conforme necessário para verificar os resultados esperados
        # Aqui, estamos apenas verificando se o arquivo CSV foi criado
        with open('output_data.csv', 'r') as file:
            content = file.read()
            self.assertTrue(content.strip())  # Verifica se o arquivo não está vazio


    def test_extract_values_from_url_success(self):
        # Escreva um teste para o caso de sucesso da função extract_values_from_url
        current_date_obj = datetime.now()
        current_date2 = current_date_obj.replace(hour=0, minute=0, second=0, microsecond=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
        current_date21 = (current_date_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime("20%Y-%m-%d_%H-%M-%SZ")
        url = f"http://10.61.6.197:8083/view/Forecast%20Values%{current_date21}.txt"

        # Chame a função extract_values_from_url com o URL de teste
        extract_values_from_url(url)

        # Adapte isso conforme necessário para verificar os resultados esperados
        # Aqui, estamos apenas verificando se o arquivo CSV foi criado
        # e se contém pelo menos uma linha
        with open('forecast_data.csv', 'r') as file:
            content = file.read()
            self.assertTrue(content.strip())  # Verifica se o arquivo não está vazio


    def test_final_file_success(self):
        # Escreva um teste para o caso de sucesso da função final_file
        objective_function = "Cost"  # Substitua com o valor desejado

        # Chame a função final_file com o objetivo de teste
        final_file(objective_function)

        # Adapte isso conforme necessário para verificar os resultados esperados
        # Aqui, estamos apenas verificando se o arquivo final foi criado
        with open('arquivo_final.csv', 'r') as file:
            content = file.read()
            self.assertTrue(content.strip())  # Verifica se o arquivo não está vazio"""


    def test_parameters(self):

        # Chame a função parameters
        parameters()

        # Adapte isso conforme necessário para verificar os resultados esperados
        # Aqui, estamos apenas verificando se os arquivos CSV foram criados
        with open('dayahead_prices.csv', 'r') as prices_file:
            prices_content = prices_file.read()
            self.assertTrue(prices_content.strip())  # Verifica se o arquivo de preços não está vazio

        with open('output_data.csv', 'r') as co2_file:
            co2_content = co2_file.read()
            self.assertTrue(co2_content.strip())  # Verifica se o arquivo de previsão de CO2 não está vazio

        with open('forecast_data.csv', 'r') as values_file:
            values_content = values_file.read()
            self.assertTrue(values_content.strip())  # Verifica se o arquivo de valores não está vazio

        with open('arquivo_final.csv', 'r') as final_file:
            final_content = final_file.read()
            self.assertTrue(final_content.strip())  # Verifica se o arquivo de valores não está vazio"""

    def test_upload_files_success(self):
        # Substitua 'caminho_do_diretorio' pelo caminho real do diretório que contém os arquivos a serem enviados
        directory_path = r"C:\Users\miguel.preto\PycharmProjects\Inputs\outputs"  # Update this path as needed
        #directory_path = "/code/outputs

        # Chame a função que você deseja testar
        try:
            upload_latest_file(directory_path)
        except Exception as e:
            self.fail(f"Error during file upload: {e}")

