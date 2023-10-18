import pandas as pd

# Carregar os arquivos CSV em dataframes
df1 = pd.read_csv("dayahead_prices.csv")
#df2 = pd.read_csv("output_data.csv")
df3 = pd.read_csv("forecast_data.xlsx")


# Concatenar os dataframes em um único dataframe
df_final = pd.concat([df1, df3], ignore_index=True)

# Salvar o dataframe em um novo arquivo CSV
df_final.to_csv("arquivo_final.csv", index=False)

print("Arquivos unidos com sucesso!")