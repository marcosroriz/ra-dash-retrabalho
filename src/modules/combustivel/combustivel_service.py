import pandas as pd
import holidays
import plotly.express as px

from ..sql_utils import *

class CombustivelService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def df_lista_combustivel_modelo(self, datas):
        '''Retorna uma lista das OSs'''
        
        # data_inicio_str = datas[0]
        # data_fim = pd.to_datetime(datas[1])
        # data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        df_lista_combus = pd.read_sql(
            f"""
            select distinct
            vec_model as "LABEL"
            from
                rmtc_viagens_analise rva
            where dia = '{datas}'
            order by
                vec_model
            """,
            self.pgEngine,
        )
        df_lista_combus.fillna({'LABEL': 'Modelo Não Informado'}, inplace=True)
        return df_lista_combus
    
    
    def df_lista_linha_rmtc(self, datas, lista_modelo):
        '''Retorna uma lista das OSs'''
        
        # data_inicio_str = datas[0]
        # data_fim = pd.to_datetime(datas[1])
        # data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_modelo = subquery_modelos_combustivel(lista_modelo)
        
        df_lista_combus = pd.read_sql(
            f"""
            select distinct 
                encontrou_numero_linha as "LABEL"  
            from 
                rmtc_viagens_analise rva 
            where 
                encontrou_numero_linha is not null and dia = '{datas}'
                {subquery_modelo}
            """,
            self.pgEngine,
        )
 
        return df_lista_combus
    
    def obter_feriados_goiania(self, ano):
        """
        Obtém os feriados nacionais, estaduais e municipais para Goiânia (GO) usando a lib holidays.
        
        Parâmetros:
        - ano (int): Ano para buscar os feriados.

        Retorna:
        - set: Conjunto de datas dos feriados em formato 'YYYY-MM-DD'.
        """
        feriados_br = holidays.Brazil(years=ano, state="GO")  # Pega feriados do Brasil, GO e Goiânia
        return set(feriados_br.keys())

    def filtrar_dias_especiais(self, df, dia):
        """
        Filtra um DataFrame deixando apenas os sábados, domingos ou feriados de Goiânia (GO).

        Parâmetros:
        - df (pd.DataFrame): DataFrame contendo uma coluna de datas.
        - dia (str): Pode ser 'sabado', 'domingo', 'feriado' ou 'todos'.

        Retorna:
        - pd.DataFrame filtrado conforme o dia especificado.
        """
        if 'dia' not in df.columns:
            raise ValueError("O DataFrame deve conter uma coluna chamada 'data'.")

        df['dia'] = pd.to_datetime(df['dia'])  # Converte para datetime
        df['dia_semana'] = df['dia'].dt.dayofweek  # Obtém o dia da semana (0=segunda, 6=domingo)

        ano = df['dia'].dt.year.unique()[0]  # Pega o ano das datas no DF
        feriados_goiania = self.obter_feriados_goiania(ano)  # Obtém feriados automaticamente
        
        df['feriado'] = df['dia'].astype(str).isin(feriados_goiania)

        if dia == 'sabado':
            return df[df['dia_semana'] == 5]
        elif dia == 'domingo':
            return df[df['dia_semana'] == 6]
        elif dia == 'feriado':
            return df[df['feriado']]
        elif dia == 'todos':
            return df
        else:
            raise ValueError("O parâmetro 'dia' deve ser 'sabado', 'domingo', 'feriado' ou 'todos'.")

    def df_tabela_combustivel(self, datas, lista_modelo, lista_linhas, sentido_linha, dia):
        # data_inicio_str = datas[0]
        # data_fim = pd.to_datetime(datas[1])
        # data_fim_str = data_fim.strftime("%Y-%m-%d")

        data_selecionada = datas
        subquery_modelo = subquery_modelos_combustivel(lista_modelo)
        subquery_linhas = subquery_linha_combustivel(lista_linhas)
        subquery_sentido = subquery_sentido_combustivel(sentido_linha)
        

        query = f"""
            WITH consumo_km_linha AS (
                SELECT 
                    encontrou_numero_linha,
                    SUM("total_comb_l") / NULLIF(SUM("tamanho_linha_km_sobreposicao"), 0) AS "CONSUMO_POR_KM_LINHA"
                FROM rmtc_viagens_analise rva
                WHERE
                dia = '{data_selecionada}'
                GROUP BY encontrou_numero_linha
            ),
            --TABELA DE MÉDIA KM_VEICULO
            consmo_km_veiculo as (
                SELECT 
                    vec_num_id,
                    SUM("total_comb_l") / NULLIF(SUM("tamanho_linha_km_sobreposicao"), 0) AS "CONSUMO_POR_KM_VEICULO"
                FROM rmtc_viagens_analise rva
                WHERE dia = '{data_selecionada}' -- FILTRAGEM PELA data !!!
                GROUP BY vec_num_id
            ),
            geral as (
            SELECT 
                rva.dia, 
                rva.vec_num_id,
                rva.encontrou_numero_linha,
                rva.encontrou_sentido_linha,
                SUM(rva."total_comb_l") / NULLIF(SUM(rva."tamanho_linha_km_sobreposicao"), 0) AS "CONSUMO_POR_KM"
            FROM rmtc_viagens_analise rva
            WHERE 
                    rva.dia = '{data_selecionada}' -- FILTRAGEM PELA data !!!
                    AND encontrou_numero_linha is not null
                    {subquery_linhas}
                    {subquery_modelo}
                    {subquery_sentido}
            GROUP BY 
                rva.dia, 
                rva.vec_num_id,
                rva.encontrou_numero_linha,
                rva.encontrou_sentido_linha
            )
            SELECT  gl.* ,
                    ckv."CONSUMO_POR_KM_VEICULO",
                    (gl."CONSUMO_POR_KM" - ckv."CONSUMO_POR_KM_VEICULO") AS "DIFERENCA_CONSUMO_KM-VEICULO_",
                    ckl."CONSUMO_POR_KM_LINHA",
                    (gl."CONSUMO_POR_KM" - ckl."CONSUMO_POR_KM_LINHA") AS "DIFERENCA_CONSUMO_KM-LINHA"
            FROM geral as gl
            LEFT JOIN consumo_km_linha ckl
                ON gl.encontrou_numero_linha = ckl.encontrou_numero_linha
            --BUSCAR O CONSUMO DA VEICULO GERAL SOMENTE FITLRANDO A DATA
            LEFT JOIN consmo_km_veiculo ckv
                ON gl.vec_num_id = ckv.vec_num_id
            """

        df_lista_combus = pd.read_sql(query, self.pgEngine, )
        
        if df_lista_combus.empty:
            return pd.DataFrame()  # Retorna um DataFrame vazio

        df_final_combustivel = self.filtrar_dias_especiais(df_lista_combus, dia[0].lower()).fillna(0).round(2)
        df_final_combustivel['dia'] = pd.to_datetime(df_final_combustivel['dia']).dt.strftime('%Y-%m-%d')
        return df_final_combustivel

    def grafico_combustivel(self, datas, lista_modelo, lista_linhas, sentido_linha, dia):
        # data_inicio_str = datas[0]
        # data_fim = pd.to_datetime(datas[1])
        # data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_modelo = subquery_modelos_combustivel(lista_modelo)
        subquery_linhas = subquery_linha_combustivel(lista_linhas)
        subquery_sentido = subquery_sentido_combustivel(sentido_linha)
        
        df = pd.read_sql(
            f"""
            --QUERY GRÁFICO v2
            SELECT TO_CHAR(dia, 'DD/MM/YYYY') AS "DIA_BR",
                vec_model as "MODELO", 
                vec_num_id as "NUMERO_VEICULO",
                km_por_litro as "KILOMETRO_POR_LTIRO",
                encontrou_timestamp_inicio as "TIME"
            FROM rmtc_viagens_analise rva
            WHERE dia = '{datas}'
                    {subquery_linhas}
                    {subquery_modelo}
                    {subquery_sentido}
            --QUERY GRÁFICO v2
            """,
            self.pgEngine,
        )
        df["TIME"] = pd.to_datetime(df["TIME"])
        numero_viagens = len(df)
        num_veiculos_diff = df['NUMERO_VEICULO'].nunique()
        num_modelo_diff = df['MODELO'].nunique()
        df = df.sort_values(by="TIME")

        fig = px.line(df, x="TIME", y="KILOMETRO_POR_LTIRO", color="MODELO",
                    title="Consumo KM/L ao Longo do Tempo por Modelo")

        return fig, numero_viagens, num_veiculos_diff, num_modelo_diff