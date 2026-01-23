import os

def findexcelfiles(folder):

    files = []
    folders = []
    elements = os.listdir(folder)

    for element in elements:
        if os.path.isdir(f"{folder}{element}"):
            folders += [f"{folder}{element}"]
        if ('.xlsx' in element) or ('xls' in element):
            files += [f"{folder}/{element}"]
    
    return files, folders
    
def findallexcelfiles(folder):
    folders = [folder]
    files = []
    while len(folders)>0:
        folders_ = []
        for folder_ in folders:
            files_new, folder_new = findexcelfiles(folder_)
            folders_ += folder_new
            files += files_new
        folders = folders_
        
    return files
