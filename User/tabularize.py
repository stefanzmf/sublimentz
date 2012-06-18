import sublime, sublime_plugin
import array, string

class TabularizeCommand(sublime_plugin.TextCommand):
   def run(self, edit):
      sels = self.view.sel()
      for sel in sels:
         if sel.empty():
            continue

         old = self.view.substr(sel)
         new = self.tabularize(old)

         edit = self.view.begin_edit();
         self.view.replace(edit, sel, new)
         self.view.end_edit(edit)

   def tabularize(self, old):
      rawRows = string.split(old, "\n")

      # spaltenanzahl validieren
      colCount = string.count(rawRows[0], "|") + 1
      for row in rawRows[1:]:
         if string.count(row, "|") != colCount - 1:
            sublime.error_message("column count does not match")
            return old

      # spaltenbreiten ermitteln
      print colCount
      widths = []
      for col in xrange(0, colCount):
         max = 0
         for row in rawRows:
            val = string.split(row, "|")[col].strip()
            vLen = len(val)
            if vLen > max:
               max = vLen
         widths.append(max)

      new = self.empty_table_line(widths)
      
      # inhaltszeilen zusammenbauen
      for row in rawRows:
         vals = string.split(row, "|")
         line = "|"
         for col in xrange(0, len(vals)):
            val = vals[col].strip()
            vLen = widths[col]
            line += " " + string.ljust(val, vLen + 1) + "|"
         new += line + "\n"
         new += self.empty_table_line(widths)

      return new

   # baut eine header-, footer- oder trennzeile
   def empty_table_line(self, widths):
      s = "+"
      for width in widths:
         s += string.replace(string.ljust("", width + 2), " ", "-")
         s += "+"
      return s + "\n"