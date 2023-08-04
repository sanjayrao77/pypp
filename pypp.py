#!/usr/bin/python3 -B

#  * github.com/sanjayrao77
#  * pypp.py - program to preprocess text files, a la m4 or cpp
#  * Copyright (C) 2023 Sanjay Rao
#  *
#  * This program is free software; you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License as published by
#  * the Free Software Foundation; either version 2 of the License, or
#  * (at your option) any later version.
#  *
#  * This program is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License
#  * along with this program; if not, write to the Free Software
#  * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys
import ast
import math
import time

whitelist_globals=[ 'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BlockingIOError', 'BrokenPipeError',
'BufferError', 'BytesWarning', 'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError', 'ConnectionRefusedError',
'ConnectionResetError', 'DeprecationWarning', 'EOFError', 'Ellipsis', 'EncodingWarning', 'EnvironmentError', 'Exception',
'False', 'FileExistsError', 'FileNotFoundError', 'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
'ImportError', 'ImportWarning', 'IndentationError', 'IndexError', 'InterruptedError', 'IsADirectoryError', 'KeyError',
'KeyboardInterrupt', 'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError', 'None', 'NotADirectoryError',
'NotImplemented', 'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning', 'PermissionError',
'ProcessLookupError', 'RecursionError', 'ReferenceError', 'ResourceWarning', 'RuntimeError', 'RuntimeWarning',
'StopAsyncIteration', 'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TimeoutError',
'True', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',
'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError',
'__build_class__', '__name__',
'abs', 'aiter', 'all', 'anext', 'any', 'ascii',
'bin', 'bool', 'breakpoint', 'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'complex', 'copyright', 'credits', 'delattr',
'dict', 'dir', 'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset', 'getattr', 'hasattr', 'hash', 'hex', 'id', 'int',
'isinstance', 'issubclass', 'iter', 'len', 'license', 'list', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'ord',
'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
'sum', 'super', 'tuple', 'type', 'vars', 'zip']

def isclean_ast(x):
    for n in ast.walk(x):
        if isinstance(n,ast.Import):
            print('Import in embedded code')
            return False
    return True

class Object():
    pass

class PyPP():
    def __init__(self,ignoreprefixes,inlineprefixes,escapeprefixes,inclusion_maxdepth,sharedvars=None):
        self.ignoreprefixes=ignoreprefixes
        self.inlineprefixes=inlineprefixes
        self.escapeprefixes=escapeprefixes
        self.includefuse=inclusion_maxdepth
        self.lines=[]
        self.execlines=[]
        self.indivert=False
        self.inexec=False
        self.sharedvars=sharedvars if sharedvars else Object()
        self.includedirs=['.']
    def set(self,name,value):
        setattr(self.sharedvars,name,value)
    def exec_process(self,text):
        ap = ast.parse(text)
        if not isclean_ast(ap): raise ValueError("Unclean embedded code")
        def out(text): 
            self.lines.append(text)
        def include(fn):
            if not self.includefuse: raise ValueError("Too much inclusion, inf loop?")
            p=PyPP(self.ignoreprefixes,self.inlineprefixes,self.escapeprefixes,self.includefuse-1,self.sharedvars)
            p.includedirs=self.includedirs
            p.include(fn)
            self.lines.extend(p.lines)
        globals={}
        bs={}
        for k in whitelist_globals: bs[k]=getattr(__builtins__,k,None)
        globals['__builtins__']=bs
        globals['out']=out
        globals['include']=include
        globals['math']=math
        globals['time']=time
        locals={}
        locals['defines']=self.sharedvars
        locals['d']=self.sharedvars
        exec(compile(ap,filename='',mode='exec'),globals,locals)
    def keylookup(self,key,default):
        v=getattr(self.sharedvars,key.lower(),None)
        if v == None:
            return default
        if callable(v): v=v(self.sharedvars)
        return str(v)
    def ismacroletter(c):
        if c.isupper(): return True
        if c.isdigit(): return True
        if c == '_': return True
        return False
    def m4replace(self,line):
        for prefix in self.inlineprefixes:
            a=line.split(prefix)
            for i in range(1,len(a)):
                s=a[i]
                j=0
                while PyPP.ismacroletter(s[j]): j+=1
                if not j: a[i]=prefix+s
                else:
                    key=s[:j]
                    v=self.keylookup(key,None)
                    if v!=None:
                        if len(s)>j+1 and s[j]=='`' and s[j+1]=='\'': j=j+2
                        a[i]=v+s[j:]
                    else:
                        a[i]=prefix+s
                        print("Key \"%s%s\" not found"%(prefix,key),file=sys.stderr)
            line=''.join(a)
        return line
    def startswitha(line,a):
        for p in a:
            if line.startswith(p): return True
        return False
    def process(self,line):
        if PyPP.startswitha(line,self.ignoreprefixes): # one-line comment is useful for xml syntax highlighting, e.g. "<PyPP#/><!--"
            pass
        elif PyPP.startswitha(line,self.escapeprefixes):
            after9=line[9:]
            if after9.startswith('divert'):
                if self.inexec: raise ValueError("Divert in exec")
                if self.indivert: raise ValueError("Double divert")
                self.indivert=True
            elif after9.startswith('exec'):
                if self.inexec: raise ValueError("Double exec")
                if self.indivert: raise ValueError("Exec in divert")
                self.inexec=True
                self.execlines=[]
            elif after9.startswith('end'):
                if self.indivert:
                    self.indivert=False
                elif self.inexec:
                    self.inexec=False
                    self.exec_process(''.join(self.execlines))
                else: raise ValueError("Unknown PyPP end: '%s'"%line)
            elif not self.indivert:
                if self.inexec: raise ValueError("Double exec") # this would work but would be asynch
                self.exec_process(after9)
            else: raise ValueError("Unprocessed PyPPP line: %s"%line)
        else:
            if self.inexec:
                if line.startswith('.'):
                    if line.startswith('. '): line=line[2:]
                    else: line=line[1:]
                self.execlines.append(line)
            elif not self.indivert:
                line=self.m4replace(line)
                self.lines.append(line)
    def add_includedir(self,dirn):
        self.includedirs.append(dirn)
    def include(self,forfn):
        f=forfn
        if isinstance(forfn,str):
            for d in self.includedirs:
                try:
                    f=open(d+'/'+forfn)
                except FileNotFoundError:
                    continue
                break
            else: raise ValueError("File not found %s"%(forfn))
        while True:
            l=f.readline()
            if not l: break
            self.process(l)
    def export(self,output):
        for l in self.lines:
            print(l,file=output,end='')

if __name__ == '__main__':
    p=PyPP(['<PyPP#'],['PyPP_','M4_'],['### PyPP ','/// PyPP '],10)
    isstdin=True
    for arg in sys.argv[1:]:
        if arg.startswith('-'):
            if arg.startswith('-D'): # define string
                a=arg[2:].split('=')
                k=a[0]
                if len(a)==1:
                    if k: p.set(k,True)
                else:
                    if k: p.set(k,''.join(a[1:]))
            elif arg.startswith('-d'): # define integer
                a=arg[2:].split('=')
                k=a[0]
                if len(a)==1:
                    if k: p.set(k,0)
                else:
                    if k: p.set(k,int(a[1]))
            elif arg.startswith('-I'): # directory to search for include(filename)
                a=arg[2:].split(',')
                for fn in a:
                    p.add_includedir(fn)
            else: raise ValueError('Unrecognized argument %s'%arg)
        else:
            isstdin=False
            p.include(arg)
    if isstdin: p.include(sys.stdin)
    p.export(sys.stdout)
