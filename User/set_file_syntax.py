import sublime, sublime_plugin, os, fnmatch

class SetFileSyntaxCommand(sublime_plugin.WindowCommand):
    def callback(self, index):
        if index >= 0:
            self.window.active_view().set_syntax_file(self.syntaxList[index][1])

    def run(self):
        self.populate_map()
        self.window.show_quick_panel(self.syntaxList, self.callback)

    def populate_map(self):
        """Get a list of valid syntax highlighting options"""
        self.syntaxList = []
        for root, dirnames, filenames in os.walk(sublime.packages_path()):
            for filename in fnmatch.filter(filenames, '*.tmLanguage'):
                name = os.path.splitext(filename)[0]
                full_path = os.path.join(root, filename)
                relative_path = full_path.replace(sublime.packages_path(), 'Packages')
                relative_path = relative_path.replace('\\', '/') # fix windows paths

                self.syntaxList.append([name, relative_path])