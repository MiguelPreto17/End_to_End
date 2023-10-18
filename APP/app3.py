import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output  # Adicionado o módulo Output
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import base64
import io
import datetime as dt


#df = pd.read_csv('input/input_data2.csv')

dateparse = lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
output = pd.read_csv('setpoints.csv', parse_dates=['datetime'], index_col='datetime', decimal=',', sep=';',
	                   date_parser=dateparse)
output.index.rename('datetime', inplace=True)

#fig1= px.bar(data, x="Date", y="load", barmode="group"),


fig3 = px.scatter(output, x="Datetime", y=['pCharge', 'pDischarge', 'eBess'])
fig3.update_traces(mode='lines+markers')


app = dash.Dash(__name__)

#['Cost', 'Life Cycle Assesment']

app.layout = html.Div(
    children=[
    html.H1(children='InterStore'),
    html.H2(' OBJECTIVE FUNCTION'),
    dcc.RadioItems(['Cost      ', 'Environmental Impact'], style=dict(display='flex'),className='radio-item'),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H2('Battery 1'),
                        dcc.Dropdown(
                            options=[
                                'Lithium', 'Vanadium', 'Lead_Acid', 'NaS', 'Supercaps', 'NiCd', 'Flywheel'
                            ]
                        )
                    ],
                    style={'margin-bottom': '20px'}
                ),
                html.Div(
                    children=[
                        html.Label('Capacity [kWh]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                ),
                html.Div(
                    children=[
                        html.Label('Maximum C-rate [0,1]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                ),
                html.Div(
                    children=[
                        html.Label('Minimum C-rate [0,1]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                )
            ],
            style={'display': 'inline-block', 'width': '45%', 'vertical-align': 'top'}
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H2('Battery 2'),
                        dcc.Dropdown(
                            options=[
                                'Lithium', 'Vanadium', 'Lead_Acid', 'NaS', 'Supercaps', 'NiCd', 'Flywheel'
                            ]
                        )
                    ],
                    style={'margin-bottom': '20px'}
                ),
                html.Div(
                    children=[
                        html.Label('Capacity [kWh]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                ),
                html.Div(
                    children=[
                        html.Label('Maximum C-rate [0,1]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                ),
                html.Div(
                    children=[
                        html.Label('Minimum C-rate [0,1]: '),
                        dcc.Input(type='text')
                    ],
                    style={'margin-bottom': '10px'}
                )
            ],
            style={'display': 'inline-block', 'width': '45%', 'vertical-align': 'top', 'margin-left': '5%'}
        ),
        html.Table(
            children=[
                html.Tr(
                    children=[
                        dcc.Input(type='text', value=f'value CO2/kWh {i + 1}')  # Célula editável
                    ]
                ) for i in range(24)
            ]
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.Upload(
                            id='upload-button1',
                            children=html.Button('Upload Load File')
                        ),
                        dcc.Graph(
                            id='graph1',
                            figure={
                                'data': [],
                                'layout': {'title': 'Graph 1'}
                            }
                        )
                    ],
                    style={'display': 'inline-block', 'width': '45%'}
                ),
                html.Div(
                    children=[
                        dcc.Upload(
                            id='upload-button2',
                            children=html.Button('Upload File 2')
                        ),
                        dcc.Graph(
                            id='graph2',
                            figure={
                                'data': [{'x': [1, 2, 3], 'y': [2, 4, 1], 'type': 'bar', 'name': 'Graph 2'}],
                                'layout': {'title': 'Graph 2'}
                            }
                        )
                    ],
                    style={'display': 'inline-block', 'width': '45%', 'margin-left': '5%'}
                )
            ],
            style={'margin-top': '20px'}
        ),
        html.Div(
            children=[
                dcc.Graph(
                    id='scatter-graph',
                    figure=fig3
                )
            ],
            style={'width': '90%', 'margin': '20px auto'}
        ),
        html.Div(
            children=[
                html.Label('  Avoided degradation % (kWh)/ Avoided CO2 emission % (g-C02/kWh) '),
                dcc.Input(type='text')
            ],
            style={'margin-bottom': '20px'}
        ),
        html.Div(
            children=[
                html.Label('  Output Final  '),
                dcc.Input(type='text')
            ],
            style={'margin-bottom': '20px'}
        ),
    ]
)

@app.callback(Output('graph1', 'figure'), [Input('upload-button1', 'contents')])
def update_graph1(contents):

    """dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y  %H:%M')
    data = pd.read_csv('input_data2.csv', parse_dates=['date'], index_col='date', decimal=',', sep=';',
                       date_parser=dateparse)
    data.index.rename('datetime', inplace=True)

    fig = px.bar(data, x="Date", y="load", barmode="group"),
    fig.update_layout(title='Graph 1')"""


    # Process the uploaded file and update the graph accordingly
    # Replace the following code with your actual file processing logic
    """if contents is not None:
        # Decode and read the CSV file from the contents
        content_type, content_string = contents.split(';')
        padding = len(content_string) % 4
        if padding > 0:
            content_string += '=' * (4 - padding)
        try:
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
     

            # Create the scatter plot using the data from the CSV file
            #fig = go.Figure(data=go.Scatter(x=df['load'], y=df['market'], mode='markers'))
            #fig.update_layout(title='graph1')

            return fig
        except Exception as e:
            print(str(e))

    else:
        return {'data': [], 'layout': {'title': 'Graph 1'}}"""

    if contents:
        return {
            'data': [{'x': [1, 2, 3], 'y': [2, 4, 1], 'type': 'bar', 'name': 'Graph 2'}],
            'layout': {'title': 'Graph 2'}
        }
    else:
        return {'data': [], 'layout': {'title': 'Load'}}

@app.callback(Output('graph2', 'figure'), [Input('upload-button2', 'contents')])
def update_graph2(contents):
    # Process the uploaded file and update the graph accordingly
    # Replace the following code with your actual file processing logic
    if contents:
        return {
            'data': [{'x': [1, 2, 3], 'y': [2, 4, 1], 'type': 'bar', 'name': 'Graph 2'}],
            'layout': {'title': 'Graph 2'}
        }
    else:
        return {'data': [], 'layout': {'title': 'Graph 2'}}

if __name__ == '__main__':
    app.run_server(debug=True)