import os

def breakdown(filepath: os.path):
    dir, fileandext = os.path.split(filepath)
    file, ext = os.path.splitext(fileandext)
    return {'dir': dir, 'filandext': fileandext, 'file': file, 'extension': ext}