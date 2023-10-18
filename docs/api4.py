import time
import configparser
import requests
import json
import mysql.connector
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import re

app = Flask(__name__)


def register_service(data):
    url = 'https://apimocha.com/testdata1/registerService'  # https://apimocha.com/testdata1/reg_service
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("Registration data sent successfully")
        print("Server response:", response.text)
        return response.json()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Error occurred: {err}')
    return None


try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="interstoredb"
    )
    cursor = db.cursor()
except Exception as e:
    print("Error connecting to the database")
    exit(1)


def create_table_if_not_exists():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS weather_predictions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        request VARCHAR(255),
        timestamp VARCHAR(255),
        k VARCHAR(255),
        engUnit VARCHAR(255),
        v FLOAT
    )
    """

    try:
        cursor.execute(create_table_query)
        db.commit()
        print("Table 'weather_predictions' created successfully (or already exists)")
    except Exception as e:
        print("Error occurred while creating the table")
        print(f"Error: {str(e)}")


def create_load_forecasts_table_if_not_exists():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS load_forecasts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        request VARCHAR(255),
        timestamp VARCHAR(255),
        k VARCHAR(255),
        engUnit VARCHAR(255),
        v FLOAT,
        srcTime INT,
        units VARCHAR(255),
        avgPwr FLOAT,
        forecastType VARCHAR(20)
    )
    """

    try:
        cursor.execute(create_table_query)
        db.commit()
        print("Table 'load_forecasts' created successfully (or already exists)")
    except Exception as e:
        print("Error occurred while creating the table")
        print(f"Error: {str(e)}")


create_load_forecasts_table_if_not_exists()

create_table_if_not_exists()
create_load_forecasts_table_if_not_exists()


def regex_pattern(string):
    now_pattern = 'datetime.utcnow\(\).isoformat\(\) \+ "Z"'
    hour_later_pattern = '\(datetime.utcnow\(\) \+ timedelta\(hours=1\)\).isoformat\(\) \+ "Z"'

    now = datetime.utcnow().isoformat() + "Z"
    hour_later = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    string = re.sub(now_pattern, f'"{now}"', string)
    string = re.sub(hour_later_pattern, f'"{hour_later}"', string)

    return string


def regex_pattern_handle(string):
    now_pattern = 'datetime.utcnow\(\).isoformat\(\) \+ "Z"'
    hour_later_pattern = '\(datetime.utcnow\(\) \+ timedelta\(hours=1\)\).isoformat\(\) \+ "Z"'
    timestamp_pattern = 'int\(datetime.utcnow\(\).timestamp\(\)\)'
    day_ago_pattern = '\(datetime.utcnow\(\) - timedelta\(days=1\)\).isoformat\(\) \+ "Z"'

    now = datetime.utcnow().isoformat() + "Z"
    hour_later = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    timestamp = int(datetime.utcnow().timestamp())
    day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"

    string = re.sub(now_pattern, f'"{now}"', string)
    string = re.sub(hour_later_pattern, f'"{hour_later}"', string)
    string = re.sub(timestamp_pattern, f'{timestamp}', string)
    string = re.sub(day_ago_pattern, f'"{day_ago}"', string)

    return string


@app.route('/weather', methods=['GET'])
def get_weather():
    print("GET /weather called")
    # removed fetch_weather() call
    return jsonify({'status': 'success', 'message': 'Weather data already fetched at start up'}), 200


def fetch_weather():
    weather_url = 'https://apimocha.com/testdata1/weather_data'

    try:
        weather_response = requests.get(weather_url, headers={'User-Agent': 'XY'})
        weather_response.raise_for_status()
        print("Weather data fetched successfully")

        response_text = regex_pattern(weather_response.text)
        print("Response:", response_text)
        weather_info = json.loads(response_text)
    except Exception as e:
        print("Error occurred while making a GET request")
        print("Error:", str(e))
        return None

    for weather_prediction in weather_info['weatherForecast']:
        insert_query = """INSERT INTO weather_predictions (request, timestamp, k, engUnit, v) 
                        VALUES (%s, %s, %s, %s, %s)"""
        params = (weather_prediction['request'], weather_prediction['timestamp'], weather_prediction['k'],
                  weather_prediction['engUnit'], weather_prediction['v'])

        print(f"Weather prediction data: {weather_prediction}")
        print(f"Query params: {params}")

        try:
            cursor.execute(insert_query, params)
            db.commit()
            print("Weather data saved to the database successfully")
        except Exception as e:
            print("Error occurred while inserting data into the database")
            print(f"Failed to insert weather prediction into database. Error: {str(e)}")

    return weather_info['weatherForecast']


@app.route('/loadForecast', methods=['POST'])
def load_forecast():
    print("POST /Load Forecast called")
    # removed fetch_load_forecast() call
    return jsonify({'status': 'success', 'message': 'Load forecast data already fetched at start up'}), 200


def fetch_load_forecast():
    loadForecast_url = 'https://apimocha.com/testdata1/load_forecast'

    try:
        loadForecast_response = requests.post(loadForecast_url, headers={'User-Agent': 'XY'})
        loadForecast_response.raise_for_status()
        print("Load Forecast data fetched successfully")

        response_text = regex_pattern_handle(loadForecast_response.text)
        print("Response:", response_text)
        loadForecast_info = json.loads(response_text)
    except Exception as e:
        print("Error occurred while making a POST request")
        print("Error:", str(e))
        return None

    for load_forecast in loadForecast_info['weatherForecast']:
        insert_query = f"""INSERT INTO load_forecasts (request, timestamp, k, engUnit, v, srcTime, forecastType) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(insert_query, (
        load_forecast['request'], load_forecast['timestamp'], load_forecast['k'], load_forecast['engUnit'],
        load_forecast['v'], loadForecast_info['srcTime'], 'weatherForecast'))
        print(f"Weather forecast data saved to the database: {load_forecast}")

    for power_measurement in loadForecast_info['powerMeasurements']:
        insert_query = f"""INSERT INTO load_forecasts (timestamp, units, avgPwr, srcTime, forecastType) 
                        VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(insert_query, (
        power_measurement['timestamp'], power_measurement['units'], power_measurement['avgPwr'],
        loadForecast_info['srcTime'], 'powerMeasurement'))
        print(f"Power measurement data saved to the database: {power_measurement}")

    db.commit()

    return {'weatherForecast': loadForecast_info['weatherForecast'],
            'powerMeasurements': loadForecast_info['powerMeasurements']}


def create_status_table_if_not_exists():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS data_status (
        id INT AUTO_INCREMENT PRIMARY KEY,
        data_fetched BOOLEAN DEFAULT FALSE
    )
    """
    try:
        cursor.execute(create_table_query)
        db.commit()
        print("Table 'data_status' created successfully (or already exists)")
    except Exception as e:
        print("Error occurred while creating the table")
        print(f"Error: {str(e)}")


create_status_table_if_not_exists()


def check_address_and_fetch_data():
    check_query = "SELECT data_fetched FROM data_status WHERE id=1"
    cursor.execute(check_query)
    result = cursor.fetchone()

    data_fetched = result[0] if result else False

    if data_fetched:
        print("Data has already been fetched and saved. Skipping.")
        return

    data = {
        "solarConfig": {
            "timeResolution": 60,
            "installedCapacity": 2000,
            "forecastHorizon": 24,
            "units": "w",
            "quantiles": [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85,
                          0.9, 0.95]
        },
        "loadConfig": {
            "timeResolution": 60,
            "forecastHorizon": 24,
            "quantiles": [0.5]
        },
        "instLocation": {
            "address": "Capwatt, Lugar do Espido, Via Norte",
            "city": "Maia",
            "country": "Portugal",
            "latitude": 41.2353648793153,
            "longitude": -8.639516824044687
        }
    }

    register_service_response = register_service(data)
    if register_service_response is None:
        print("Failed to register the service")
    else:
        if (register_service_response['instLocation']['address'].lower() == data['instLocation']['address'].lower() and
                register_service_response['instLocation']['city'].lower() == data['instLocation']['city'].lower() and
                register_service_response['instLocation']['country'].lower() == data['instLocation'][
                    'country'].lower()):
            print("Address matched. Fetching weather and load forecast data.")
            fetch_weather()
            fetch_load_forecast()

            update_query = "INSERT INTO data_status (id, data_fetched) VALUES (1, True) ON DUPLICATE KEY UPDATE data_fetched=True"
            try:
                cursor.execute(update_query)
                db.commit()
                print("Data fetch and save status updated successfully in the database")
            except Exception as e:
                print("Error occurred while updating data fetch and save status in the database")
                print(f"Failed to update status. Error: {str(e)}")
        else:
            print("Address didn't match")


check_address_and_fetch_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
