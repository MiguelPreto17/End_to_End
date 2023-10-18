import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import dash_table

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Input(id='data-input', type='number', value=''),
    dcc.RadioItems(
        id='option1',
        options=[
            {'label': 'Opção A', 'value': 'A'},
            {'label': 'Opção B', 'value': 'B'},
        ],
        value='A'
    ),
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Valor 1', 'value': 'valor1'},
            {'label': 'Valor 2', 'value': 'valor2'},
        ],
        value='valor1'
    ),
    html.Button('Enviar Dados', id='submit-button'),
    html.Div(id='data-output'),

    dash_table.DataTable(
        id='editable-table',
        columns=[
            {'name': 'Valor 1', 'id': 'valor1'},
            {'name': 'Valor 2', 'id': 'valor2'},
            {'name': 'Valor 3', 'id': 'valor3'},
            {'name': 'Valor 4', 'id': 'valor4'},
            {'name': 'Valor 5', 'id': 'valor5'},
        ],
        data=[
            {'valor1': 0, 'valor2': 0, 'valor3': 0, 'valor4': 0, 'valor5': 0},
        ],
        editable=True
    ),

    dcc.Graph(id='chart'),
])


@app.callback(
    dash.dependencies.Output('data-output', 'children'),
    dash.dependencies.Output('chart', 'figure'),
    dash.dependencies.Input('submit-button', 'n_clicks'),
    dash.dependencies.State('data-input', 'value'),
    dash.dependencies.State('option1', 'value'),
    dash.dependencies.State('dropdown', 'value'),
    dash.dependencies.State('editable-table', 'data'),
)



def send_data(n_clicks, input_value, selected_option, dropdown_value, table_data):

    table_data_to_send = []
    for row in table_data:
        row_values = [row[column_name] for column_name in ['valor1', 'valor2', 'valor3', 'valor4', 'valor5']]
        #row_values = [row[column_name] for column_name in table_data]
        table_data_to_send.append(row_values)

    if n_clicks:
        url1 = f"http://localhost:8000/api/objective_function"
        data1 = {
            "selected_option": selected_option,
        }
        response1 = requests.post(url1, data=data1)

        url2 = f"http://localhost:8000/api/settings"
        data2 = {
            "input_value": float(input_value),
            "table_data": table_data_to_send
        }
        response2 = requests.post(url2, data=data2)

        url3 = f"http://localhost:8000/api/teste"
        data3 = {
            "selected_option": selected_option,
            "input_value": float(input_value),
        }
        response3 = requests.post(url3, data=data3)

        if response1.status_code == 200 and response2.status_code == 200 and response3.status_code == 200:
            return f" Resultado 2: {response2.json()['message']}"
        else:
            return "Falha ao enviar dados"


def update_chart(figure):
    response = requests.get("http://localhost:8000/api/get_data_for_chart")
    if response.status_code == 200:
        data = response.json()["data"]
        figure = {
            'data': [
                {'x': list(range(1, len(data) + 1)), 'y': data, 'type': 'line', 'name': 'Data'}
            ],
            'layout': {
                'title': 'Gráfico de Dados'
            }
        }
        return figure
    else:
        raise dash.exceptions.PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True)