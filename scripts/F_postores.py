import pandas as pd

postor = pd.read_pickle('../data/interim/postor.pickle')
adjudicaciones = pd.read_pickle('../data/interim/adjudicaciones.pickle')

df_adjudicaciones = adjudicaciones[['codigoconvocatoria', 'n_item', 'ruc_proveedor']].drop_duplicates()
df_adjudicaciones['cn'] = df_adjudicaciones['codigoconvocatoria'].astype(str) + '-' + df_adjudicaciones['n_item'].astype(str)
df_adjudicaciones = df_adjudicaciones.drop(columns=['codigoconvocatoria', 'n_item']).set_index('cn')
df_postor = postor[['codigo_convocatoria', 'n_item', 'ruc_codigo_postor', 'postor']]
df_postor['cn'] = df_postor['codigo_convocatoria'].astype(str) + '-' + df_postor['n_item'].astype(str)
df_postor = df_postor.set_index('cn')

df_join = df_adjudicaciones.join(df_postor, how='left')
df_join['ganador_flag'] = (df_join['ruc_proveedor'] == df_join['ruc_codigo_postor']) *1

df_join.to_csv('../data/processed/F_postores.csv', sep='|', index=False)