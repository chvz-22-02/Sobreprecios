import pandas as pd

entidades = pd.read_pickle('../data/interim/entidades.pickle')
adjudicaciones = pd.read_pickle('../data/interim/adjudicaciones.pickle')

df_adjudicaciones = adjudicaciones[['codigoentidad', 'tipoentidad']].set_index('codigoentidad')
df_entidades = entidades[['RUC', 'NOMBRE_DE_ENTIDAD', 'DEPARTAMENTO', 'PROVINCIA', 'DISTRITO', 'CODCONSUCODE']].set_index('CODCONSUCODE')

df_entidades.join(df_adjudicaciones, how='left').to_csv('../data/processed/D_entidades.csv', sep='|', index=True)