import unittest
from datetime import datetime, timedelta
from API_Inputs.dayahead_prices import extract_prices
from API_Inputs.emissions import extract_co2_forecast
from API_Inputs.Forecast import extract_values_from_url
from API_Inputs.Final_file import final_file
from Parametrs import parameters
from database import upload_latest_files
from main import optimize


class TestParameters(unittest.TestCase):
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
        #directory_path = r"C:\Users\miguel.preto\PycharmProjects\Inputs\outputs"  # Update this path as needed
        directory_path = "/code/outputs"

        # Chame a função que você deseja testar
        try:
            upload_latest_files(directory_path)
        except Exception as e:
            self.fail(f"Error during file upload: {e}")

