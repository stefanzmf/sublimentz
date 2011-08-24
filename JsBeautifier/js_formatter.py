import sublime, sublime_plugin, jsbeautifier

class JsFormatCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		opts = jsbeautifier.default_options();
		opts.indent_char = "\t"
		opts.indent_size = 1
		opts.max_preserve_newlines = 5
		selection = self.view.sel()[0]
		replaceRegion = selection if len(selection) > 0 else sublime.Region(0, self.view.size())
		res = jsbeautifier.beautify(self.view.substr(replaceRegion), opts)
		self.view.replace(edit, replaceRegion, res)
