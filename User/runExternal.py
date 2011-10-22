import sublime, sublime_plugin, subprocess, os

class runExternalCommand(sublime_plugin.EventListener):
   def on_post_save(self, view):

     if not view.file_name().strip().startswith('C:\\temp\\'):
       return

     if os.name == "nt":
       startupinfo = subprocess.STARTUPINFO()
       startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

     process = subprocess.Popen(('G:/dev tools/putty.exe', '', '', view.file_name()),
     stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
     print('PREDITOR UPDATED: ' + view.file_name().replace('C:\\temp\\', ''))