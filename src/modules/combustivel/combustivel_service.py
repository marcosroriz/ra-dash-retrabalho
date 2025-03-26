import pandas as pd 

from ..sql_utils import *

class CombustivelService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def df_lista_combustivel_modelo(self, datas):
        '''Retorna uma lista das OSs'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        df_lista_combus = pd.read_sql(
            f"""
            select distinct
            vec_model as "LABEL"
            from
                rmtc_viagens_analise rva
            where dia between '{data_inicio_str}' AND '{data_fim_str}'
            order by
                vec_model
            """,
            self.pgEngine,
        )
        df_lista_combus.fillna({'LABEL': 'Modelo Não Informado'}, inplace=True)
        return df_lista_combus
    
    
    def df_lista_linha_rmtc(self, datas, lista_modelo):
        '''Retorna uma lista das OSs'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_modelo = subquery_modelos_combustivel(lista_modelo)
        
        df_lista_combus = pd.read_sql(
            f"""
            select distinct 
                encontrou_numero_linha as "LABEL"  
            from 
                rmtc_viagens_analise rva 
            where 
                encontrou_numero_linha is not null and dia between '{data_inicio_str}' and '{data_fim_str}'
                {subquery_modelo}
            """,
            self.pgEngine,
        )
        print(f"""
            select distinct 
                encontrou_numero_linha as "LABEL"  
            from 
                rmtc_viagens_analise rva 
            where 
                encontrou_numero_linha is not null and dia between '{data_inicio_str}' and '{data_fim_str}'
                {subquery_modelo}
            """)
        return df_lista_combus
    
    def df_grafico_combustivel():
        pass