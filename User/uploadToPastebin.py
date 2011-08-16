import sublime, sublime_plugin, httplib, urllib, re

class uploadToPastebinCommand( sublime_plugin.TextCommand ):
  def run( self, view ):
    try:
      s = re.findall(r'\bphp|html|css|xml|haml|python|js|java|css|c\+\+|cs|c\b', self.view.scope_name(0))[0]
      if s == 'js':
        s = 'javascript'
      if s == 'cs':
        s = 'csharp'
      if s == 'c++':
        s = 'cpp'
    except:
      s = 'other'

    c, v, i = self.view.substr(sublime.Region(0, self.view.size())), self.view.sel()[0], 0
    if v.begin() != v.end():
      for x in self.view.lines(v):
        b = x.begin()+i
        c = c[:b] + '@@' + c[b:]
        i = i + 2
       
    r, p = httplib.HTTPConnection('www.pastebin.com'), urllib.urlencode({'paste_private': 1, 'paste_code': c, 'paste_format': s})
    h = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    r.request("POST", "/api_public.php", p, h)
    g = r.getresponse()
    if g.status == 200:
      l = g.read()
      if l[0:5] == 'ERROR':
        sublime.status_message('Something went wrong:\n' + l)
      else:
        sublime.set_clipboard(l)
        sublime.status_message('Link has been copied to your clipboard')
    else:
      sublime.status_message('Something went wrong: ' + g.status, g.reason)
    r.close()
