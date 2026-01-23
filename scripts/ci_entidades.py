import pandas as pd

entidades = pd.read_csv('../data/raw/entidades_contratantes.csv', sep='|', encoding='latin-1')
entidades.to_pickle("../data/interim/entidades.pickle")