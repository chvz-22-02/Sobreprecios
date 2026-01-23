import pandas as pd

adjudicaciones = pd.read_pickle('../data/interim/adjudicaciones.pickle')
convocatorias = pd.read_pickle('../data/interim/convocatorias.pickle')

df_adjudicaciones = adjudicaciones[['codigoconvocatoria', 'n_item', 'codigoentidad', 'ruc_proveedor', 'objetocontractual', 'tipoprocesoseleccion', 
                                    'proceso', 'descripcion_proceso', 'unidad_medida', 'cantidad_adjudicado_item', 'estado_item', 
                                    'descripcion_item', 'fecha_convocatoria', 'fecha_buenapro', 'fecha_consentimiento_bp', 
                                    'monto_referencial_item_soles', 'monto_adjudicado_item_soles']]
df_adjudicaciones['cn'] = df_adjudicaciones['codigoconvocatoria'].astype(str) + '-' + df_adjudicaciones['n_item'].astype(str)
df_adjudicaciones = df_adjudicaciones.set_index('cn')
df_convocatorias = convocatorias[['codigoconvocatoria', 'n_item', 'departamento_item', 'provincia_item', 'distrito_item', 
                                  'itemcubso']].drop_duplicates()
df_convocatorias['cn'] = df_convocatorias['codigoconvocatoria'].astype(str) + '-' + df_convocatorias['n_item'].astype(str)
df_convocatorias = df_convocatorias.drop(columns=['codigoconvocatoria', 'n_item']).set_index('cn')

df_adjudicaciones.join(df_convocatorias, how='left').to_csv('../data/processed/F_adjudicaciones.csv', sep='|', index=True)