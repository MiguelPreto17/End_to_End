import pandas as pd

def final_file(Objective_function):

    # Carregar os arquivos CSV em dataframes
    df1 = pd.read_csv("dayahead_prices.csv", sep=";")
    df2 = pd.read_csv("output_data.csv", sep=";")
    df3 = pd.read_csv("forecast_data.csv", sep=";" )

    # Converter a coluna 'date' para o tipo datetime
    df1['date'] = pd.to_datetime(df1['date'])

    # Adicionar uma hora à coluna de datas para começar na 00:00
    start_date = pd.to_datetime(df1['date'].iloc[0]) + pd.DateOffset(hours=1)  # Adiciona uma hora ao primeiro timestamp
    df1['date'] = pd.date_range(start=start_date, periods=len(df1), freq='H')  # Começa na meia-noite
    print(df1)

    # Removendo "kW" da coluna
    df3['Load'] = df3['Load'].str.replace(' kW', '')

    # Convertendo a coluna para o tipo numérico (float)
    df3['Load'] = pd.to_numeric(df3['Load'], errors='coerce')

    # Removendo linhas com valores nulos (NaN)
    df3 = df3.dropna()

    # Redefinindo os índices
    df3 = df3.reset_index(drop=True)

    print(df3['Load'])

    # Criar um novo DataFrame com as colunas desejadas
    df_final = pd.DataFrame(columns=["date", "pv", "market", "feedin", "load"])

    # Preencher as colunas do novo DataFrame com os dados dos DataFrames originais


    if Objective_function == "Cost":
        df_final["date"] = df1["date"]  # Coluna DateTime de df1
        df_final["market"] = df1["Price"] / 1000 # Coluna Price de df1
        df_final["pv"] = 0
        df_final["feedin"] = 0
        df_final["load"] = df3["Load"]

    else:
        df_final["date"] = df1["date"]  # Coluna DateTime de df1
        df_final["market"] = df2["Value"]  # Coluna Price de df1
        df_final["pv"] = 0
        df_final["feedin"] = 0
        df_final["load"] = df3["Load"]

    df_final['market'] = df_final['market'].replace('[^\d.,]', '', regex=True)

    # Substituindo vírgulas por pontos nas colunas 'market' e 'load'
    df_final['market'] = df_final['market'].astype(str).str.replace('.', ',')
    df_final['load'] = df_final['load'].astype(str).str.replace('.', ',')

    # Selecionando as primeiras 24 linhas do DataFrame df_final
    df_primeiras_24 = df_final.iloc[:24, :]

   # Salvar o dataframe em um novo arquivo CSV
    df_primeiras_24.to_csv("arquivo_final.csv", index=False, sep=";")
    print("Arquivos unidos com sucesso!")
    print(df_primeiras_24)



