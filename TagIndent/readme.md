Sublime Text
------------------

This repository holds a Sublime Text 2 Plugin. See: http://www.sublimetext.com/

Description
------------------

Apply and/or add beauty indentation to HTML/XML/RDF/XUL tags found on selection(s). Pure unobtrusive and simple RegExp implementation.

Usage 
------------------

There is context menuitems called "Indent Tags on Selection", "Indent Tags on Document"

There is also Main menuitems: Edit -> Tag -> "Indent Tags on Selection", "Indent Tags on Document"

There is also commands "Indent Tags on Selection", "Indent Tags on Document"

Aims 
------------------

Aims to add and/or apply correct indentation to little portions of HTML or XML, not to complete documents.

Information
------------------

It takes the starting "indentation level" from the first line of each selection and sums tabs as needed.

On empty tags, and on tags with less than 40 characters, it writes the tag in one line.

Short-cut is "ctrl+shift+h"

Source / Installation 
------------------

https://github.com/SublimeText/TagIndent