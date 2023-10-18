import pandas as pd

# Carregar os arquivos CSV em dataframes
df1 = pd.read_csv("dayahead_prices.csv",sep=";")
df2 = pd.read_csv("output_data.csv")
df3 = pd.read_csv("forecast_data.csv", sep=";" )


# Criar um novo DataFrame com as colunas desejadas
df_final = pd.DataFrame(columns=["DateTime", "Date", "Value", "Price"])

# Preencher as colunas do novo DataFrame com os dados dos DataFrames originais
df_final["DateTime"] = df1["DateTime"]  # Coluna DateTime de df1
df_final["Price"] = df1["Price"]  # Coluna Price de df1
df_final["Date"] = df3["Date"]  # Coluna DateTime de df3 (renomeada para Date)
df_final["Value"] = df3["Value"]  # Coluna Value de df3

# Salvar o dataframe em um novo arquivo CSV
df_final.to_csv("arquivo_final.csv", index=False, sep=";")

print("Arquivos unidos com sucesso!")

