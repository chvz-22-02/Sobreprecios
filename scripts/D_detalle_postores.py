import pandas as pd

proveedores = pd.read_pickle('../data/interim/proveedores.pickle')
consorcio = pd.read_pickle('../data/interim/consorcio.pickle')
adjudicaciones = pd.read_pickle('../data/interim/adjudicaciones.pickle')

df_proveedores = proveedores[['RUC PROVEEDOR','proveedor','registro','departamento','provincia','distrito']]
df_proveedores['RUC'] = df_proveedores['RUC PROVEEDOR']
df_proveedores['consorcio_flag'] = 0
df_proveedores = df_proveedores.rename(columns={'RUC PROVEEDOR':'RUC_ind',
                                                'proveedor': 'proveedor_ind'})
df_proveedores = df_proveedores.set_index('RUC')
df_adjudicaciones = adjudicaciones[['ruc_proveedor', 'tipo_proveedor']].set_index('ruc_proveedor')
df_consorcio = consorcio[['ruc_consorcio','miembro','ruc_miembro']].set_index('ruc_miembro')
df_consorcio = df_consorcio.join(df_proveedores, how='left').drop(columns=['RUC_ind'])
df_consorcio = df_consorcio.reset_index(drop=False).rename(columns={'ruc_miembro':'RUC_ind','ruc_consorcio':'RUC'})
df_consorcio = df_consorcio.drop(columns=['proveedor_ind']).rename(columns={'miembro':'proveedor_ind'})
df_consorcio['consorcio_flag'] = 1
df_proveedores = df_proveedores.reset_index(drop=False)
df_consorcio = df_consorcio.fillna({'registro':'Sin información', 'departamento':'Sin información', 'provincia':'Sin información', 'distrito':'Sin información'})
df_consorcio.columns = df_proveedores.columns.tolist()

pd.concat([df_proveedores, df_consorcio], ignore_index=True).to_csv('../data/processed/D_detalle_postores.csv', sep='|', index=False)