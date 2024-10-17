import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread 
import webbrowser
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder

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

def plotar_listas_analise(df_ref, coluna_df_ref, subheader):

    lista_ref = df_ref[coluna_df_ref].unique().tolist()

    st.subheader(subheader)

    container = st.container(height=200, border=True)

    selecao = container.radio('', sorted(lista_ref), index=None)

    return selecao

def montar_df_analise_mensal(df_ref, coluna_ref, info_filtro):

    df_mensal = df_ref[(df_ref[coluna_ref] == info_filtro)].groupby('ano_mes')\
        .agg({'Consumo estimado': 'count', 'Titularidade': 'sum', 'ano': 'first', 'mes': 'first', 'Colaborador': 'first'}).reset_index()

    df_mensal = df_mensal.rename(columns = {'Consumo estimado': 'serviços', 'Colaborador': 'colaborador'})

    df_mensal['performance'] = round(df_mensal['Titularidade'] / df_mensal['serviços'], 2)

    df_mensal = df_mensal.sort_values(by = ['ano', 'mes']).reset_index(drop = True)

    return df_mensal

def criar_coluna_performance(df_resumo_performance):

    df_resumo_performance['Performance'] = round(df_resumo_performance['Titularidade'] / df_resumo_performance['Rota'], 2)

    df_resumo_performance = df_resumo_performance.sort_values(by='Performance', ascending=False)

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].astype(float) * 100

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].apply(lambda x: f'{x:.0f}%')

    df_resumo_performance = df_resumo_performance.rename(columns={'Rota': 'Serviços'})

    return df_resumo_performance

st.set_page_config(layout='wide')

st.title('Performance Diária Titularidade - Natal')

st.divider()

if 'df_motoristas' not in st.session_state:

    criar_dfs_excel()

row0 = st.columns(2)

row1 = st.columns(1)

row2 = st.columns(2)

row3 = st.columns(1)

row4 = st.columns(2)

with row0[0]:

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

with row0[1]:

    atualizar_dfs_excel = st.button('Atualizar Dados')

if atualizar_dfs_excel:

    criar_dfs_excel()

if data_inicial and data_final:

    df_filtro_data = st.session_state.df_historico[(st.session_state.df_historico['Apenas Data']>=data_inicial) & 
                                                   (st.session_state.df_historico['Apenas Data']<=data_final)].reset_index(drop=True)
    
    df_filtro_data['Titularidade'] = 0
    
    mask_titularidade = (df_filtro_data['Colaborador']==df_filtro_data['Titular']) | (df_filtro_data['Colaborador']==df_filtro_data['Folguista'])
    
    df_filtro_data.loc[mask_titularidade, 'Titularidade']=1

    with row1[0]:

        st.divider()

    df_resumo_titularidade = df_filtro_data.groupby('Tipo de Veiculo').agg({'Titularidade': 'sum', 'Rota': 'count'}).reset_index()

    df_resumo_titularidade = criar_coluna_performance(df_resumo_titularidade)

    gb = GridOptionsBuilder.from_dataframe(df_resumo_titularidade)
    gb.configure_selection('single')
    gb.configure_grid_options(domLayout='autoHeight')
    gridOptions = gb.build()

    with row2[0]:

        grid_response = AgGrid(df_resumo_titularidade, gridOptions=gridOptions, 
                                enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    selected_rows = grid_response['selected_rows']

    if selected_rows is not None and len(selected_rows)>0:

        tipo_veiculo = selected_rows['Tipo de Veiculo'].iloc[0]

        if tipo_veiculo:

            df_resumo_titularidade_veiculo = df_filtro_data[df_filtro_data['Tipo de Veiculo']==tipo_veiculo].groupby('Veiculo')\
                    .agg({'Titularidade': 'sum', 'Rota': 'count'}).reset_index()
            
            df_resumo_titularidade_veiculo = criar_coluna_performance(df_resumo_titularidade_veiculo)

            gb = GridOptionsBuilder.from_dataframe(df_resumo_titularidade_veiculo)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row2[1]:

                grid_response = AgGrid(df_resumo_titularidade_veiculo, gridOptions=gridOptions, 
                                    enable_enterprise_modules=False, fit_columns_on_grid_load=True)

