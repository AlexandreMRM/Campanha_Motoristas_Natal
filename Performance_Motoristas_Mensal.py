import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread 
import webbrowser
from datetime import datetime
import matplotlib.pyplot as plt
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

    st.session_state.df_frota['Veiculo'] = st.session_state.df_frota['Veiculo'].astype(str)

    st.session_state.df_historico = st.session_state.df_historico[st.session_state.df_historico['Veículo']!='Total'].reset_index(drop=True)

    for index in range(len(st.session_state.df_historico)):

        if pd.isna(st.session_state.df_historico.at[index, 'Veículo']):

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

def plotar_listas_analise(df_ref, coluna_df_ref, subheader):

    lista_ref = df_ref[coluna_df_ref].unique().tolist()

    st.subheader(subheader)

    container = st.container(height=200, border=True)

    selecao = container.radio('', sorted(lista_ref), index=None)

    return selecao

def montar_df_analise_mensal(df_ref, coluna_ref, info_filtro):

    df_mensal = df_ref[(df_ref[coluna_ref] == info_filtro)].groupby('ano_mes')\
        .agg({'Consumo estimado': 'count', 'meta_batida': 'sum', 'ano': 'first', 'mes': 'first', 'Colaborador': 'first'}).reset_index()

    df_mensal = df_mensal.rename(columns = {'Consumo estimado': 'serviços', 'Colaborador': 'colaborador'})

    df_mensal['performance'] = round(df_mensal['meta_batida'] / df_mensal['serviços'], 2)

    df_mensal = df_mensal.sort_values(by = ['ano', 'mes']).reset_index(drop = True)

    return df_mensal

def grafico_duas_barras_linha_percentual(referencia, eixo_x, eixo_y1, label1, eixo_y2, label2, eixo_y3, label3, 
                                          titulo):
    fig, ax1 = plt.subplots(figsize=(15, 8))

    bar_width = 0.35
    posicao_barra1 = np.arange(len(referencia[eixo_x]))
    posicao_barra2 = posicao_barra1 + bar_width

    ax1.bar(posicao_barra1, referencia[eixo_y1], width=bar_width, label=label1, edgecolor = 'black', linewidth = 1.5)

    ax1.bar(posicao_barra2, referencia[eixo_y2], width=bar_width, label=label2, edgecolor = 'black', linewidth = 1.5)

    for i in range(len(referencia[eixo_x])):
        texto1 = str(int(referencia[eixo_y1][i]))
        ax1.text(posicao_barra1[i], referencia[eixo_y1][i], texto1, ha='center', va='bottom')

    for i in range(len(referencia[eixo_x])):
        texto2 = str(int(referencia[eixo_y2][i]))
        ax1.text(posicao_barra2[i], referencia[eixo_y2][i], texto2, ha='center', va='bottom')

    ax2 = ax1.twinx()
    ax2.plot(referencia[eixo_x], referencia[eixo_y3], linestyle='-', color='black', label=label3, \
    linewidth = 0.5)

    for i in range(len(referencia[eixo_x])):
        texto = str(int(referencia[eixo_y3][i] * 100)) + "%"
        ax2.text(referencia[eixo_x][i], referencia[eixo_y3][i], texto, ha='center', va='bottom')

    # Configurações dos eixos x e legendas
    ax1.set_xticks(posicao_barra1 + bar_width / 2)
    ax1.set_xticklabels(referencia[eixo_x])
    
    ax1.set_ylim(top=max(referencia[eixo_y1]) * 3)
    ax2.set_ylim(bottom = 0, top=max(referencia[eixo_y3]) + .05)
    
    plt.title(titulo, fontsize=30)

    plt.xlabel('Ano/Mês')
    ax1.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    ax2.legend(loc='lower right', bbox_to_anchor=(1.2, 1))

    st.pyplot(fig)
    plt.close(fig)

def plotar_listas_sub_analise(df_ref, coluna_filtro, info_filtro, coluna_radio, titulo_radio):

    df_mes_atual = df_ref[(df_ref['ano']==ano_atual) & (df_ref['mes']==mes_atual) & (df_ref[coluna_filtro]==info_filtro)].reset_index(drop=True)

    lista_ref = df_mes_atual[coluna_radio].unique().tolist()

    row3 = st.columns(2)
    
    with row3[0]:

        selecao = st.radio(titulo_radio, sorted(lista_ref), index=None)

    return selecao, df_mes_atual, row3

def plotar_tabela_mes_atual(df_ref, coluna_group, dict_colunas):

    df_mes_atual = df_ref[(df_ref['ano']==ano_atual) & (df_ref['mes']==mes_atual) & (df_ref['Veiculo']==veiculo)].reset_index(drop=True)

    df_group = df_mes_atual.groupby(coluna_group).agg({'Consumo estimado':'count', 'meta_batida': 'sum'}).reset_index()

    df_group = df_group.rename(columns=dict_colunas)

    df_group['Performance'] = round(df_group['Metas Batidas']/df_group['Serviços'], 2)
    
    for index, value in df_group['Performance'].items():

            df_group.at[index, 'Performance'] = f'{str(int(value*100))}%'

    container_dataframe = st.container()

    container_dataframe.dataframe(df_group, hide_index=True, use_container_width=True)

st.set_page_config(layout='wide')

st.title('Performance Mensal Motoristas - Natal')

st.divider()

if 'df_motoristas' not in st.session_state:

    criar_dfs_excel()

row0 = st.columns(2)

row2 = st.columns(1)

with row0[0]:

    data_atual = datetime.now()
    ano_atual = data_atual.year
    mes_atual = data_atual.month

    ano_analise = st.number_input('Ano', step=1, value=ano_atual, key='ano_analise')

    mes_analise = st.number_input('Mês', step=1, value=mes_atual, key='mes_analise')

with row0[1]:

    atualizar_dfs_excel = st.button('Atualizar Dados')

    percentual_apoios = st.number_input('Desconto Percentual p/ Metas em Apoios', step=1, value=10)

    percentual_apoios = percentual_apoios/100

if atualizar_dfs_excel:

    criar_dfs_excel()

if ano_analise and mes_analise:

    df_filtro_data = st.session_state.df_historico[(st.session_state.df_historico['ano']==ano_analise) & 
                                                   (st.session_state.df_historico['mes']==mes_analise)].reset_index(drop=True)

    for index in range(len(df_filtro_data)):

        rota = df_filtro_data.at[index, 'Rota']

        if rota=='Apoio':

            df_filtro_data.at[index, 'Consumo estimado'] = df_filtro_data.at[index, 'Consumo estimado']*(1-percentual_apoios)
    
    df_filtro_data['meta_batida'] = df_filtro_data.apply(lambda row: 1 if row['Consumo real'] >= row['Consumo estimado'] else 0, axis = 1)
    
    with row0[0]:
    
        tipo_analise = st.radio('Tipo de Análise', ['Motorista', 'Tipo de Veículo'], index=None)

    with row0[1]:

        if tipo_analise=='Motorista':

            motorista = plotar_listas_analise(df_filtro_data, 'Colaborador', 'Motoristas')

        elif tipo_analise=='Tipo de Veículo':

            tipo_de_veiculo = plotar_listas_analise(df_filtro_data, 'Tipo de Veiculo', 'Tipos de Veículos')
        
    if tipo_analise=='Tipo de Veículo' and tipo_de_veiculo:

        df_tipo_veiculos = montar_df_analise_mensal(df_filtro_data, 'Tipo de Veiculo', tipo_de_veiculo)

        with row2[0]:

            st.divider()

            grafico_duas_barras_linha_percentual(df_tipo_veiculos, 'ano_mes', 'serviços', 'Serviços', 'meta_batida', 'Metas Batidas', 'performance', 'Performance', 
                                                tipo_de_veiculo)
            
        st.divider()

        veiculo, df_mes_atual, row3 = plotar_listas_sub_analise(df_filtro_data, 'Tipo de Veiculo', tipo_de_veiculo, 'Veiculo', 'Veículos')

        if veiculo:

            row2 = st.columns(1)

            df_veiculos = montar_df_analise_mensal(df_filtro_data, 'Veiculo', veiculo)

            with row2[0]:

                grafico_duas_barras_linha_percentual(df_veiculos, 'ano_mes', 'serviços', 'Serviços', 'meta_batida', 'Metas Batidas', 'performance', 'Performance', 
                                                    veiculo)
                
            st.divider()

            plotar_tabela_mes_atual(df_filtro_data, 'Colaborador', 
                                    {'Veiculo': 'Veículo', 'Consumo estimado': 'Serviços', 'meta_batida': 'Metas Batidas'})

    elif tipo_analise=='Motorista' and motorista:

        df_motorista = montar_df_analise_mensal(df_filtro_data, 'Colaborador', motorista)

        with row2[0]:

            st.divider()

            grafico_duas_barras_linha_percentual(df_motorista, 'ano_mes', 'serviços', 'Serviços', 
                                                'meta_batida', 'Metas Batidas', 'performance', 'Performance', 
                                                motorista)
            
        st.divider()

        tipo_veiculo, df_motorista_mes_atual, row3 = plotar_listas_sub_analise(df_filtro_data, 'Colaborador', motorista, 
                                                                            'Tipo de Veiculo', 'Tipos de Veículos')

        if tipo_veiculo:

            df_tipo_veiculo = df_motorista_mes_atual[df_motorista_mes_atual['Tipo de Veiculo']==tipo_veiculo].reset_index(drop=True)

            df_tipo_veiculo_final = df_tipo_veiculo.groupby('Veiculo').agg({'Consumo estimado':'count', 'meta_batida': 'sum'}).reset_index()

            df_tipo_veiculo_final = df_tipo_veiculo_final.rename(columns={'Veiculo': 'Veículo', 'Consumo estimado': 'Serviços', 'meta_batida': 'Metas Batidas'})

            df_tipo_veiculo_final['Performance'] = round(df_tipo_veiculo_final['Metas Batidas']/df_tipo_veiculo_final['Serviços'], 2)

            for index, value in df_tipo_veiculo_final['Performance'].items():

                df_tipo_veiculo_final.at[index, 'Performance'] = f'{str(int(value*100))}%'

            df_tipo_veiculo_final_2 = df_tipo_veiculo.groupby('Tipo de Veiculo').agg({'Consumo estimado':'count', 'meta_batida': 'sum'}).reset_index()

            df_tipo_veiculo_final_2 = df_tipo_veiculo_final_2.rename(columns={'Tipo de Veiculo': 'Tipo de Veículo', 'Consumo estimado': 'Serviços', 
                                                                                'meta_batida': 'Metas Batidas'})

            df_tipo_veiculo_final_2['Performance'] = round(df_tipo_veiculo_final_2['Metas Batidas']/df_tipo_veiculo_final_2['Serviços'], 2)

            for index, value in df_tipo_veiculo_final_2['Performance'].items():

                df_tipo_veiculo_final_2.at[index, 'Performance'] = f'{str(int(value*100))}%'

            with row3[1]:

                st.dataframe(df_tipo_veiculo_final_2, hide_index=True)

                st.dataframe(df_tipo_veiculo_final, hide_index=True)
