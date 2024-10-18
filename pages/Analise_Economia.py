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

def criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, coluna_merge):
        
    df_resumo_performance_tipo_veiculo['Km/l | Período Atual'] = \
        round(df_resumo_performance_tipo_veiculo['Distância de abastecimento'] / df_resumo_performance_tipo_veiculo['Quantidade'], 2)
    
    df_resumo_performance_tipo_veiculo_base['Km/l | Período Base'] = \
        round(df_resumo_performance_tipo_veiculo_base['Distância de abastecimento'] / df_resumo_performance_tipo_veiculo_base['Quantidade'], 2)
    
    df_resumo_performance_tipo_veiculo_geral = pd.merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, on=coluna_merge, how='left')
    
    df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] = round((df_resumo_performance_tipo_veiculo_geral['Distância de abastecimento_x'] / 
                                                                        df_resumo_performance_tipo_veiculo_geral['Km/l | Período Base']) - 
                                                                        df_resumo_performance_tipo_veiculo_geral['Quantidade_x'], 0)
    
    df_resumo_performance_tipo_veiculo_geral['Valor Litro'] = round(df_resumo_performance_tipo_veiculo_geral['Valor total'] / 
                                                                    df_resumo_performance_tipo_veiculo_geral['Quantidade_x'], 2)
    
    df_resumo_performance_tipo_veiculo_geral['Economia em R$'] = df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] * df_resumo_performance_tipo_veiculo_geral['Valor Litro']
    
    df_resumo_performance_tipo_veiculo_geral_colunas = \
        df_resumo_performance_tipo_veiculo_geral[[coluna_merge, 'Km/l | Período Base', 'Km/l | Período Atual', 'Economia em Litros', 'Valor Litro', 
                                                'Economia em R$']]
    
    return df_resumo_performance_tipo_veiculo_geral_colunas

st.set_page_config(layout='wide')

st.title('Análise de Economia - Natal')

st.divider()

if 'df_motoristas' not in st.session_state:

    criar_dfs_excel()

row0 = st.columns(2)

row1 = st.columns(2)

row2 = st.columns(1)

row3 = st.columns(2)

row4 = st.columns(2)

with row0[0]:

    atualizar_dfs_excel = st.button('Atualizar Dados')

with row1[0]:

    st.subheader('Comparar período de:')

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

with row1[1]:

    st.subheader('Em relação à:')

    data_inicial_base = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial_base')

    data_final_base = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final_base')

if atualizar_dfs_excel:

    criar_dfs_excel()

if data_inicial and data_final and data_inicial_base and data_final_base:

    with row2[0]:

        st.divider()

    df_base = st.session_state.df_historico[(st.session_state.df_historico['Apenas Data']>=data_inicial_base) & 
                                            (st.session_state.df_historico['Apenas Data']<=data_final_base)].reset_index(drop=True)
    
    df_filtro_data = st.session_state.df_historico[(st.session_state.df_historico['Apenas Data']>=data_inicial) & 
                                                   (st.session_state.df_historico['Apenas Data']<=data_final)].reset_index(drop=True)

    df_resumo_performance_tipo_veiculo = df_filtro_data.groupby('Tipo de Veiculo')\
        .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
    
    df_resumo_performance_tipo_veiculo_base = df_base.groupby('Tipo de Veiculo')\
        .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
    
    df_resumo_performance_tipo_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, 
                                                                        'Tipo de Veiculo')

    gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_tipo_veiculo_geral_colunas)
    gb.configure_selection('single')
    gb.configure_grid_options(domLayout='autoHeight')
    gridOptions = gb.build()

    with row3[0]:

        grid_response = AgGrid(df_resumo_performance_tipo_veiculo_geral_colunas, gridOptions=gridOptions, 
                                enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    selected_rows = grid_response['selected_rows']

    if selected_rows is not None and len(selected_rows)>0:

        tipo_veiculo = selected_rows['Tipo de Veiculo'].iloc[0]

        if tipo_veiculo:

            df_resumo_performance_veiculo = df_filtro_data[df_filtro_data['Tipo de Veiculo']==tipo_veiculo].groupby('Veiculo')\
                .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_base = df_base[df_base['Tipo de Veiculo']==tipo_veiculo].groupby('Veiculo')\
                .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_veiculo, df_resumo_performance_veiculo_base, 
                                                                        'Veiculo')
            
            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_veiculo_geral_colunas)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row3[1]:

                grid_response = AgGrid(df_resumo_performance_veiculo_geral_colunas, gridOptions=gridOptions, 
                                    enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                veiculo = selected_rows_2['Veiculo'].iloc[0]
                
                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Veiculo']==veiculo) & 
                                                                         (df_filtro_data['Tipo de Veiculo']==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_base = df_base[(df_base['Veiculo']==veiculo) & 
                                                                              (df_base['Tipo de Veiculo']==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_motorista_veiculo, 
                                                                                       df_resumo_performance_motorista_veiculo_base, 'Colaborador')

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo_geral_colunas)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row3[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo_geral_colunas, gridOptions=gridOptions, enable_enterprise_modules=False, 
                                            fit_columns_on_grid_load=True)
