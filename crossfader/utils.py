import typing as t

from PyQt6.QtCore import QByteArray


def filenameFilter(name: str, formats: t.List[QByteArray]) -> str:
    fileFormatList = ['*.%s' % ba.data().decode() for ba in formats]

    if fileFormatList:
        fileFormatList.append('*')
    else:
        fileFormatList.sort()

    return '%s (%s)' % (name, ' '.join(fileFormatList))
