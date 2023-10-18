"""Building measurements: http://127.0.0.1:5000/api/v1/data/building_measurements
Load forecasts: http://127.0.0.1:5000/api/v1/data/load_forecasts
Weather data: http://127.0.0.1:5000/api/v1/data/weather_data"""

from flask import Flask, jsonify
from flaskext.mysql import MySQL
import csv
import os

app = Flask(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'interstoredb'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)

def query_to_dict(cursor, rows):
    headers = [i[0] for i in cursor.description]
    result = []
    for row in rows:
        rowData = {}
        for i in range(len(headers)):
            rowData[headers[i]] = row[i]
        result.append(rowData)
    return result

def write_to_csv(filename, cursor, rows):
    # Save to CSV file
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([i[0] for i in cursor.description])  # write headers
        writer.writerows(rows)

# Route for building_measurements
@app.route('/api/v1/data/building_measurements', methods=['GET'])
def get_building_measurements():
    conn = mysql.connect()
    cursor = conn.cursor()

    query = "SELECT * FROM building_measurements"
    cursor.execute(query)

    rows = cursor.fetchall()
    data = query_to_dict(cursor, rows)
    resp = jsonify(data)
    resp.status_code = 200

    write_to_csv('building_measurements.csv', cursor, rows)

    return resp

# Route for load_forecasts
@app.route('/api/v1/data/load_forecasts', methods=['GET'])
def get_load_forecasts():
    conn = mysql.connect()
    cursor = conn.cursor()

    query = "SELECT * FROM load_forecasts"
    cursor.execute(query)

    rows = cursor.fetchall()
    data = query_to_dict(cursor, rows)
    resp = jsonify(data)
    resp.status_code = 200

    write_to_csv('load_forecasts.csv', cursor, rows)

    return resp

# Route for weather_data
@app.route('/api/v1/data/weather_data', methods=['GET'])
def get_weather_data():
    conn = mysql.connect()
    cursor = conn.cursor()

    query = "SELECT * FROM weather_predictions"
    cursor.execute(query)

    rows = cursor.fetchall()
    data = query_to_dict(cursor, rows)
    resp = jsonify(data)
    resp.status_code = 200

    write_to_csv('weather_data.csv', cursor, rows)

    return resp

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')