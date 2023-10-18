import shutil

from dash import Dash, dash_table, html, dcc
import plotly.express as px
import pandas as pd
import datetime as dt

app = Dash(__name__)

# Read data in .csv as a dataframe; read index as datetime
dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y  %H:%M')
data = pd.read_csv('input_data2.csv', parse_dates=['date'], index_col='date', decimal=',', sep=';',
	                   date_parser=dateparse)
data.index.rename('datetime', inplace=True)

dateparse = lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
output = pd.read_csv('setpoints.csv', parse_dates=['datetime'], index_col='datetime', decimal=',', sep=';',
	                   date_parser=dateparse)
output.index.rename('datetime', inplace=True)



fig = px.bar(data, x="Date", y="load", barmode="group")

fig2 = px.bar(data, x="Date", y="market", barmode="group")

fig3 = px.scatter(output, x="Datetime", y=['pCharge', 'pDischarge', 'eBess'])
fig3.update_traces(mode='lines+markers')

params = ['value CO2/kWh']

app.layout = html.Div(children=[

    html.H1(children='InterStore'),

    dcc.RadioItems(['Cost', 'Life Cycle Assesment'], style=dict(display='flex')),

    html.Br(),

    html.H2(children='Battery 1'),

    dcc.Dropdown(['Lithium', 'Vanadium', 'Lead_Acid', 'NaS', 'Supercaps', 'NiCd', 'Flywheel']),

    html.Br(),

    html.H2([
    "Capacity [kWh]: ",
    dcc.Input(id='my-input', value='initial value', type='text'),
    html.Br(),

    "Maximum C-rate [0,1]: ",
    dcc.Input(id='my-input', value='initial value', type='text'),
    html.Br(),

    "Minimum C-rate [0,1]: ",
    dcc.Input(id='my-input', value='initial value', type='text')
    ]),
    #html.Br(),

    html.H3(children='Battery 2'),

    dcc.Dropdown(['Lithium', 'Vanadium', 'Lead_Acid', 'NaS', 'Supercaps', 'NiCd', 'Flywheel']),
    html.Br(),

    html.H3([
        "Capacity2 [kWh]: ",
        dcc.Input(id='my-input', value='initial value', type='text'),
        html.Br(),

        "Maximum C-rate2 [0,1]: ",
        dcc.Input(id='my-input', value='initial value', type='text'),
        html.Br(),

        "Minimum C-rate2 [0,1]: ",
        dcc.Input(id='my-input', value='initial value', type='text')
    ]),
    html.Br(),
]), """style={'display': 'inline-block', 'width': '45%', 'margin-left': '5%'}),"""

                    html.Div(
                        children=[

                    html.H1(children='Life Cycle Assesment'),

                    dash_table.DataTable(
                            id='table-editing-simple',
                            columns=(
                                [{'id': 'Date', 'name': 'Date'}] +
                                [{'id': p, 'name': p} for p in params]
                            ),
                            data=[
                                dict(Model=i, **{param: 0 for param in params})
                                for i in range(1, 25)
                            ],
                            editable=True, style_data={
                                                        'color': 'black',
                                                        'backgroundColor': 'white',
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            'if': {'row_index': 'odd'},
                                                            'backgroundColor': 'rgb(220, 220, 220)',
                                                        }
                                                    ],
                                                    style_header={
                                                        'backgroundColor': 'rgb(210, 210, 210)',
                                                        'color': 'black',
                                                        'fontWeight': 'bold'
                                                    }),

                    html.H1(children='Load'),

                    dcc.Upload(html.Button('Upload Load File')),

                    html.Br(),



                    dcc.Graph(id='example-graph', figure=fig),

                    dcc.Graph(id='example-graph', figure=fig2),

                    dcc.Graph(id='example-graph', figure=fig3),



                ]),

if __name__ == '__main__':
    app.run_server(debug=True)