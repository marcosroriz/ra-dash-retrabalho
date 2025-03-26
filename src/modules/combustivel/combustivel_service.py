import pandas as pd 

class CombustivelService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def df_lista_combustivel_modelo(self, datas):
        '''Retorna uma lista das OSs'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        df_lista_os = pd.read_sql(
            f"""
            SELECT DISTINCT
            "DESCRICAO DO MODELO" as "LABEL"
            FROM 
                mat_view_retrabalho_10_dias mvrd 
            WHERE  "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            ORDER BY
                "DESCRICAO DO MODELO"
            """,
            self.pgEngine,
        )
        return df_lista_os