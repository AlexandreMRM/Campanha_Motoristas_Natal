import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread 
import webbrowser
from datetime import datetime
import numpy as np

def criar_dfs_excel():

    nome_credencial = st.secrets["CREDENCIAL_SHEETS"]
    credentials = service_account.Credentials.from_service_account_info(nome_credencial)
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = credentials.with_scopes(scope)
    client = gspread.authorize(credentials)
    
    spreadsheet = client.open_by_key('1m0qYTv7b0RIz9uqCrIuzRzLxc43Kz1utzLATv0HO8n0')

    lista_abas = ['BD - Motoristas', 'BD - Frota | Tipo', 'BD - Historico']

    lista_df_hoteis = ['df_motoristas', 'df_frota', 'df_historico']

    for index in range(len(lista_abas)):

        aba = lista_abas[index]

        df_hotel = lista_df_hoteis[index]
        
        sheet = spreadsheet.worksheet(aba)

        sheet_data = sheet.get_all_values()

        st.session_state[df_hotel] = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])

    st.session_state.df_historico['Consumo real'] = st.session_state.df_historico['Consumo real'].str.replace(',', '.')

    st.session_state.df_historico['Consumo real'] = pd.to_numeric(st.session_state.df_historico['Consumo real'], errors='coerce')

    st.session_state.df_historico['Consumo estimado'] = st.session_state.df_historico['Consumo estimado'].str.replace(',', '.')

    st.session_state.df_historico['Consumo estimado'] = pd.to_numeric(st.session_state.df_historico['Consumo estimado'], errors='coerce')

    st.session_state.df_historico['Distância de abastecimento'] = \
    pd.to_numeric(st.session_state.df_historico['Distância de abastecimento'], errors='coerce')

    st.session_state.df_historico['Quantidade'] = st.session_state.df_historico['Quantidade'].str.replace(',', '.')

    st.session_state.df_historico['Quantidade'] = \
    pd.to_numeric(st.session_state.df_historico['Quantidade'], errors='coerce')

    st.session_state.df_historico['Valor total'] = st.session_state.df_historico['Valor total'].str.replace('R$ ', '')

    st.session_state.df_historico['Valor total'] = st.session_state.df_historico['Valor total'].str.replace('.', '')

    st.session_state.df_historico['Valor total'] = st.session_state.df_historico['Valor total'].str.replace(',', '.')

    st.session_state.df_historico['Valor total'] = \
    pd.to_numeric(st.session_state.df_historico['Valor total'], errors='coerce')

    st.session_state.df_historico['Percentual do Estimado'] = st.session_state.df_historico['Percentual do Estimado'].str.replace(',', '.')

    st.session_state.df_historico['Percentual do Estimado'] = \
    pd.to_numeric(st.session_state.df_historico['Percentual do Estimado'], errors='coerce')

    st.session_state.df_frota['Veiculo'] = st.session_state.df_frota['Veiculo'].astype(str)

    st.session_state.df_historico = st.session_state.df_historico[st.session_state.df_historico['Veículo']!='Total'].reset_index(drop=True)

    for index in range(len(st.session_state.df_historico)):

        if st.session_state.df_historico.at[index, 'Veículo']=='':

            st.session_state.df_historico.at[index, 'Veículo']=st.session_state.df_historico.at[index-1, 'Veículo']

    lista_motoristas_historico = st.session_state.df_historico['Colaborador'].unique().tolist()

    for motorista in lista_motoristas_historico:

        if motorista in st.session_state.df_motoristas['Motorista Sofit'].unique().tolist():

            st.session_state.df_historico.loc[st.session_state.df_historico['Colaborador']==motorista, 'Colaborador']=\
                st.session_state.df_motoristas.loc[st.session_state.df_motoristas['Motorista Sofit']==motorista, 'Motorista Análise'].values[0]

    st.session_state.df_historico['Data'] = pd.to_datetime(st.session_state.df_historico['Data'], format='%d/%m/%Y %H:%M:%S')
    
    st.session_state.df_historico['ano'] = st.session_state.df_historico['Data'].dt.year

    st.session_state.df_historico['mes'] = st.session_state.df_historico['Data'].dt.month

    st.session_state.df_historico['ano_mes'] = st.session_state.df_historico['mes'].astype(str) + '/' + \
            st.session_state.df_historico['ano'].astype(str).str[-2:]
    
    st.session_state.df_historico = st.session_state.df_historico.rename(columns={'Veículo': 'Veiculo'})
    
    st.session_state.df_historico = pd.merge(st.session_state.df_historico, st.session_state.df_frota, on='Veiculo', how='left')

    st.session_state.df_historico['Apenas Data'] = st.session_state.df_historico['Data'].dt.date

st.set_page_config(layout='wide')

st.title('Abastecimentos com Anomalias - Natal')

st.divider()

row0 = st.columns(1)

if 'df_motoristas' not in st.session_state:

    criar_dfs_excel()

with row0[0]:

    atualizar_dfs_excel = st.button('Atualizar Dados')

    percentual_anomalias = st.number_input('Variação Percentual p/ Anomalia', step=1, value=30)

    percentual_anomalias = percentual_anomalias/100

df_filtro_colunas = st.session_state.df_historico[['Data', 'Despesa', 'Veiculo', 'Consumo real', 'Consumo estimado', 'Percentual do Estimado']]

df_filtro_colunas['Percentual do Estimado'] = df_filtro_colunas['Percentual do Estimado']/100

df_filtro_colunas['Perc - 1'] = df_filtro_colunas['Percentual do Estimado']-1

df_filtro_colunas.loc[(df_filtro_colunas['Perc - 1'] > percentual_anomalias) | (df_filtro_colunas['Perc - 1'] < -percentual_anomalias), 'Anomalia']='X'

df_filtro_colunas = df_filtro_colunas[df_filtro_colunas['Anomalia']=='X'].reset_index(drop=True)

df_filtro_colunas = df_filtro_colunas.rename(columns={'Veiculo': 'Veículo', 'Consumo real': 'Média km/l', 'Consumo estimado': 'Meta km/l'})

container_dataframe = st.container()

container_dataframe.dataframe(df_filtro_colunas[['Data', 'Despesa', 'Veículo', 'Média km/l', 'Meta km/l']], hide_index=True, use_container_width=True)

