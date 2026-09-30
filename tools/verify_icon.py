"""Verify EXE icon resources and its bundled Tk icon are the same ICO.

Read-only Windows build validation; does not launch the app or touch the game.
"""
import argparse
from pathlib import Path
import struct
import win32api
import win32con
from PyInstaller.archive.readers import CArchiveReader


def verify(exe,icon):
    raw=icon.read_bytes()
    reserved,kind,count=struct.unpack_from('<HHH',raw)
    assert (reserved,kind)==(0,1)
    source={}
    for index in range(count):
        width,height,_,_,_,_,length,offset=struct.unpack_from('<BBBBHHII',raw,6+index*16)
        source[(width or 256,height or 256)]=raw[offset:offset+length]
    module=win32api.LoadLibraryEx(str(exe.resolve()),0,win32con.LOAD_LIBRARY_AS_DATAFILE)
    try:
        names=win32api.EnumResourceNames(module,14)
        assert len(names)==1, names
        group=win32api.LoadResource(module,14,names[0])
        assert struct.unpack_from('<HHH',group)==(0,1,count)
        found=set()
        for index in range(count):
            width,height,_,_,_,_,length,resource_id=struct.unpack_from('<BBBBHHIH',group,6+index*14)
            size=(width or 256,height or 256)
            payload=win32api.LoadResource(module,3,resource_id)
            assert len(payload)==length
            assert payload==source[size], size
            found.add(size)
        assert found==set(source)
        manifest=win32api.LoadResource(module,24,1)
        assert b'PerMonitorV2' in manifest
    finally:
        win32api.FreeLibrary(module)
    archive=CArchiveReader(str(exe.resolve()))
    asset=next(name for name in archive.toc if name.replace('\\','/')=='assets/fish-clear.ico')
    assert archive.extract(asset)==raw
    print(f'Verified {count} exact EXE icon frames: {sorted(found)}')
    print('Bundled window icon matches EXE icon; PerMonitorV2 manifest retained.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('exe',type=Path)
    parser.add_argument('--icon',type=Path,default=Path(__file__).resolve().parents[1]/'assets'/'fish-clear.ico')
    args=parser.parse_args()
    verify(args.exe,args.icon)
