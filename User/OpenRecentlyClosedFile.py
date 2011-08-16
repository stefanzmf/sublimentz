import sublime, sublime_plugin
import os

HISTORY_SETTINGS_FILE = "History.sublime-settings"
HISTORY_MAX_ENTRIES=500

def get_history(setting_name):
    """load the history using sublime's built-in functionality for accessing settings"""
    history = sublime.load_settings(HISTORY_SETTINGS_FILE)
    if history.has(setting_name):
        return history.get(setting_name)
    else:
        return []

def set_history(setting_name, setting_values):
    """save the history using sublime's built-in functionality for accessing settings"""
    history = sublime.load_settings(HISTORY_SETTINGS_FILE)
    history.set(setting_name, setting_values)
    sublime.save_settings(HISTORY_SETTINGS_FILE)


class OpenRecentlyClosedFileEvent(sublime_plugin.EventListener):
    """class to keep a history of the files that have been opened and closed"""

    def on_close(self, view):
        self.add_to_history(view, "closed", "opened")

    def on_load(self, view):
        self.add_to_history(view, "opened", "closed")

    def add_to_history(self, view, add_to_setting, remove_from_setting):
        filename = os.path.normpath(view.file_name())
        if filename != None:
            add_to_list = get_history(add_to_setting)
            remove_from_list = get_history(remove_from_setting)

            # remove this file from both of the lists
            while filename in remove_from_list:
                remove_from_list.remove(filename)
            while filename in add_to_list:
                add_to_list.remove(filename)

            # add this file to the top of the "add_to_list" (but only if the file actually exists)
            if os.path.exists(filename):
                add_to_list.insert(0, filename)

            # write the history back (making sure to limit the length of the histories)
            set_history(add_to_setting, add_to_list[0:HISTORY_MAX_ENTRIES])
            set_history(remove_from_setting, remove_from_list[0:HISTORY_MAX_ENTRIES])

class OpenRecentlyClosedFileCommand(sublime_plugin.WindowCommand):
    """class to either open the last closed file or show a quick panel with the file access history (closed files first)"""

    def run(self, show_quick_panel=False):
        self.reload_history()
        if show_quick_panel:
            self.window.show_quick_panel(self.file_list, self.open_file)
        else:
            self.open_file(0)

    def reload_history(self):
        history = sublime.load_settings(HISTORY_SETTINGS_FILE)
        self.file_list = get_history("closed") + get_history("opened")

    def open_file(self, index):
        if index >= 0 and len(self.file_list) > index:
            self.window.open_file(self.file_list[index])
