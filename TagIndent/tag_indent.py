import sublime, sublime_plugin
import re

#to find on which indentation level we currently are
current_indentation_re = re.compile("^\s*")

#to leave additional new lines as is
aditional_new_lines_re = re.compile("^\s*\n+\s*\n+\s*$")

#possible self closing tags:       XML-------------------------- HTML------------------------------------------------HTML5----------------
self_closing_tags = re.compile("^<(\?xml|\!DOCTYPE|\!ENTITY|\!--|area|base|br|col|frame|hr|img|input|link|meta|param|command|embed|source)", re.I)

def TagIndentBlock(data, view):
		
		#the indent character
		if view.settings().get('translate_tabs_to_spaces') :
			indent_character = ' '*int(view.settings().get('tab_size', 4))
		else:
			indent_character = '\t'

		#on which indentation level we currently are?
		indentation_level = (current_indentation_re.search(data).group(0)).split("\n")
		current_indentation = indentation_level.pop()
		if len(indentation_level) == 1:
			beauty = "\n"+indentation_level[0]
		elif len(indentation_level) > 1:
			beauty = "\n".join(indentation_level)
		else:
			beauty = ''
		
		#first newline should be skipped
		starting = True

		#inspiration from http://jyro.blogspot.com/2009/08/makeshift-xml-beautifier-in-python.html
		fields = re.split('(<[^>]+>)',data)

		level = 0
		for i, f in enumerate(fields):
			if f.strip() == '':
				if aditional_new_lines_re.match(f):
					beauty += '\n'
				continue
			if f[0]=='<' and f[1] != '/':
				#	beauty += '1'
				if starting == False:
					beauty += '\n'
				starting = False
				beauty += current_indentation
				beauty += indent_character*level + f.strip()
				level = level + 1
				#self closing tag
				if f[-2:] == '/>' or self_closing_tags.match(f):
					#beauty += '2'
					beauty += current_indentation
					level = level - 1
			elif f[:2]=='</':
				level = level - 1
				#beauty += '3'
				if starting == False:
					beauty += '\n'
				starting = False
				beauty += current_indentation
				beauty += indent_character*level + f.strip()
			else:
				#beauty += '4'
				if starting == False:
					beauty += '\n'
				starting = False
				beauty += current_indentation
				beauty += indent_character*level + f.strip()

		#put empty tags on same line
		beauty = re.sub(r'<([^/][^>]*[^/])>\s+</', '<\\1></', beauty)
		#put empty tags on same line for tags with one character
		beauty = re.sub(r'<([^/])>\s+</', '<\\1></', beauty)

		#put tags with little content on same line
		beauty = re.sub(r'<([^/][^>]*[^/])>\s*([^<\t\n]{1,40})\s*</', '<\\1>\\2</', beauty)
		#put tags with little content on same line for tags with one character
		beauty = re.sub(r'<([^/])>\s*([^<\t\n]{1,40})\s*</', '<\\1>\\2</', beauty)

		return beauty

class TagIndentCommand(sublime_plugin.TextCommand):
	def run(self, edit):

		for region in self.view.sel():
			if region.empty():
				continue

			dataRegion = sublime.Region(self.view.line(region.begin()).begin(), region.end())

			data = TagIndentBlock(self.view.substr(dataRegion), self.view)

			self.view.replace(edit, dataRegion, data);

class TagIndentDocumentCommand(sublime_plugin.TextCommand):
	def run(self, edit):

		dataRegion = sublime.Region(0, self.view.size())

		data = TagIndentBlock(self.view.substr(dataRegion), self.view)

		self.view.replace(edit, dataRegion, data);
