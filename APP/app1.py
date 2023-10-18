import dash
import dash_core_components as dcc
import dash_html_components as html
import requests

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
        ],        value='valor1'
    ),
    html.Button('Enviar Dados', id='submit-button'),
    html.Div(id='data-output'),
])

@app.callback(
    dash.dependencies.Output('data-output', 'children'),
    dash.dependencies.Input('submit-button', 'n_clicks'),
    dash.dependencies.State('data-input', 'value'),
    dash.dependencies.State('option1', 'value'),
    dash.dependencies.State('dropdown', 'value')
)
def send_data(n_clicks, input_value, selected_option, dropdown_value):
    if n_clicks and input_value is not None:
        url = f"http://localhost:8000/api/receive_data"
        params = {
            "input_value": float(input_value),
            "selected_option": selected_option,
            "dropdown_value": dropdown_value
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return f"Resultado: {response.json()['message']}"
        else:
            return "Falha ao enviar dados"

if __name__ == '__main__':
    app.run_server(debug=True)