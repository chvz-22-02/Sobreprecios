import pandas as pd
import pickle
from utils import findallexcelfiles

folder = "../data/raw/"
files = [file for file in findallexcelfiles(folder) if ('CONOSCE_PROVEEDORES' in file) and not("~$" in file)]
data = [*map(lambda file: pd.read_excel(file, header = 0, dtype = str).assign(ORIGEN = file), files)]
pickle.dump(pd.concat(data), open("../data/interim/proveedores.pickle",'wb'))