# pypp, Python Pre-Processor

## Overview

This can be used as a generic text preprocessor, similarly to m4 or the C preprocessor.
I like m4 but complex logic is tricky and some of the syntax is archaic.

This uses standard Python for embedded logic so the syntax is modern and additional
functionality is trivial.

## Installing

All you need is pypp.py. You can download it to a standard unix system with python3 installed.
After a quick "chmod +x" you can run it as-is or you can import it into your own python program.

For the sake of security, you can scan the code to see that there isn't anything malicious. It's
currently less than 200 lines.

## Sandboxing and security

Embedded python code in included files will be executed. That's part of the functionality. To prevent
malicious behavior, in the included code, importing is disabled and some built-in functions are
missing (e.g. open and exec).

This sandboxing is probably **not** secure. I block the escape methods I'm aware of but there may be ways
around the sandboxing. However, basic clean-to-read embedded code is likely to be safe.

I do **not** attempt to detect infinite loops. If there's an infinite loop in included code then the processing
will hang.

## Usage

Inline replacements should start with a "M4_" or "PyPP_" prefix. These are configurable as PyPP.inlineprefixes
in the code.

Start-of-line commands should start with "### PyPP " or "/// PyPP ". These are configurable as PyPP.escapeprefixes
in the code. Special commands are "exec", "divert" and "end" to define blocks of commands. See the examples below for
more explanation. You can use "### PyPP " for python, bash, etc. and "/// PyPP " for C-like languages.

Start-of-line ignored lines should start with "<PyPP#". These are configurable as PyPP.ignoreprefixes in the code.
This is useful for hiding python code from your text editor's syntax highlighter. See the XML example below.

## Command line arguments

Command line arguments can be used to specify variable values and inclusion directories.
These will only be activated if pypp.py is run directly. If you import pypp.py and use class PyPP, these arguments
won't be processed (but you can specify them through code).

All of these arguments may be used 0 or more times.

### -Dxxx

The argument "-Dxxx" will define xxx as True.

### -Dxxx=yyy

The argument "-Dxxx=yyy" will define xxx as the string 'yyy'. You should use lowercase variable names here and reference them
as capitalized in the inline-processed text files.

If you use this for testable values, note that many strings are __True__. E.g., -Disactive=0 will set defines.isactive='0' which
will test as True (if defines.isactive: print('is true')). You should use -dxxx=yyy instead of -Dxxx=yyy for such booleans.

### -dxxx=yyy

The argument "-dxxx=yyy" will define xxx as the integer yyy, instead of as a string. This is useful for testing boolean values 
and for doing arithmetic.

### -Ix,y,z

The argument "-Ix,y,z" will add "x", "y" and "z" as search directories for any filename passed to include(). Directories with
commas in them will probably not work.


## Examples

### Inline text replacement

Keywords in the source text can be replaced with static values or function return values. The keywords (by default)
must start with M4_ or PyPP_ and be uppercase, digits or underscores. The variables in Python will be lowercase.

You can use `' as a delimiter. On successful replacement, this delimiter will be excluded in output.

Keywords that are not replaced will pass through to stdout with a message to stderr.

examples/example1.txt:
```
Hi world, I am M4_STATUS.
I am also PyPP_STATUS.
Doubled, I'm PyPP_STATUS`'PyPP_STATUS.
I am _not_ PyPP_NONAME.
### PyPP # This line will be ignored. The next one sets a value going forward
### PyPP defines.example1_value='We are %s.'%defines.status
```

Command:
```bash
./pypp.py -Dstatus=alive examples/example1.txt 
```

Output (stdout):
```
Hi world, I am alive.
I am also alive.
Doubled, I'm alivealive.
I am _not_ PyPP_NONAME.
```

Output (stderr):
```
Key "PyPP_NONAME" not found
```

### File inclusion

Additional text files can be included by using the "include(filename)" command. Those files will also be processed
with the current settings. If the included files change variables, those new values will be retained. There is
a maximum inclusion depth to avoid infinite loops.

examples/example2.txt:
```
This is example2, including example1:
"
### PyPP include('examples/example1.txt')
"

That was example 1, it gave us "PyPP_EXAMPLE1_VALUE".
```

Command:
```bash
./pypp.py -Dstatus=alive examples/example2.txt
```

Output:
```
This is example2, including example1:
"
Hi world, I am alive.
I am also alive.
Doubled, I'm alivealive.
I am _not_ PyPP_NONAME.
"

That was example 1, it gave us "We are alive.".
```

### One-line command

Single commands can be escaped on a single line to avoid code blocks. For more complex commands, you can
use a block as shown in the next example.

examples/example3.txt:
```
This is example 3.

### PyPP out('This was processed at %s.\n'%time.ctime())
```

Command:
```bash
./pypp.py examples/example3.txt
```

Output:
```
This is example 3.

This was processed at Fri Aug  4 13:26:49 2023.
```

### Block text replacement

The previous example was a command on a single line. For more complicated replacements, you can use blocks.

examples/example4.txt:
```
### PyPP divert
This will not be included in the output. You can use divert for comments or
to temporarily disable exec blocks.
### PyPP end
### PyPP exec
# you can read values from the 'defines' variable
# if you change values in 'defines', they will persist for future reference

out('Our status is %s.\n'%defines.status)
a=list(defines.status.upper())
out('Our modified status is %s.\n'%'_'.join(a))

### PyPP end
```

Command:
```bash
./pypp.py -Dstatus=alive examples/example4.txt
```

Output:
```
Our status is alive.
Our modified status is A_L_I_V_E.
```

### XML escape example

examples/example5.txt:
```
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
<PyPP#/><!--
### PyPP exec
out('\t<TextView\n')
out('\t\tandroid:text="%s" android:textSize="%s"\n'%(defines.text,defines.textsize))
out('\t\tandroid:layout_width="match_parent" android:layout_height="wrap_content" />\n')
### PyPP end -->
</LinearLayout>
```

Command:
```bash
cat examples/example5.txt | ./pypp.py -Dtext=Magic -Dtextsize=20sp
```

Output:
```
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
	<TextView
		android:text="Magic" android:textSize="20p"
		android:layout_width="match_parent" android:layout_height="wrap_content" />
</LinearLayout>
```

### Importing into your own Python

Instead of running pypp.py directly, you can use the class PyPP in your own code. This gives you control over what
prefixes are used and also allows you do define substitions via function calls (instead of static strings). It also
allows you to create custom functions available to included files.

examples/example6.txt:
```
#!/usr/bin/python3 -B

import sys
import pypp

def mystatus(defines):
	return 'embedded'

def mycounter(defines):
    defines._counter+=1
    return defines._counter

def myresetcounter(defines):
    defines._counter=0
    return 0

o=pypp.Object()
o.resetcounter=myresetcounter
o.status=mystatus
o._counter=0
o.counter=mycounter
p=pypp.PyPP(['<PyPP#'],['PyPP_'],['### PyPP'],10,o)
p.add_includedir('examples')
p.include('example6a.txt')
p.export(sys.stdout)
```

examples/example6a.txt:
```
Hi world, I am PyPP_STATUS.
Counter: PyPP_COUNTER
Counter: PyPP_COUNTER
Counter: PyPP_COUNTER
### PyPP exec
defines.resetcounter(defines)
### PyPP end
Counter: PyPP_COUNTER
```

Command:
```bash
cat examples/example6.txt | python3 -B
```

Output:
```
Hi world, I am embedded.
Counter: 1
Counter: 2
Counter: 3
Counter: 1
```

### Adding functions

For security, You can't __import__ within included python code. If you want to provide I/O or other functionality to
included python code, that can be done by creating wrappers and then passing the functions to class PyPP. You
can see example 6 above to see how this is done.
