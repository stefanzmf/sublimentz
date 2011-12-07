import sublime
import sublime_plugin

import sys
import os

sys.path.append(os.path.join(sublime.packages_path(), 'Vintage'))

import re
import subprocess
import tempfile

try:
    import ctypes
except ImportError:
    ctypes = None

import ex_range

from vintage import g_registers


GLOBAL_RANGES = []


def handle_not_implemented():
    sublime.status_message('VintageEx: Not implemented')


def set_register(text, register):
    global g_registers
    if register == '*' or register == '+':
        sublime.set_clipboard(text)
    elif register == '%':
        pass
    else:
        reg = register.lower()
        append = (reg != register)

        if append and reg in g_registers:
            g_registers[reg] += text
        else:
            g_registers[reg] = text


def filter_region(txt, command):
    try:
        contents = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        contents.write(txt.encode('utf-8'))
        contents.close()

        script = tempfile.NamedTemporaryFile(suffix='.bat', delete=False)
        script.write('@echo off\ntype %s | %s' % (contents.name, command))
        script.close()

        p = subprocess.Popen(['cmd.exe', '/C', script.name],
                                                    stdout=subprocess.PIPE)

        rv = p.communicate()
        return rv[0].decode(get_oem_cp()).replace('\r\n', '\n')[:-1]
    finally:
        os.remove(script.name)
        os.remove(contents.name)


def gather_buffer_info(v):
    """gathers data to be displayed by :ls or :buffers
    """
    path = v.file_name()
    if path:
        parent, leaf = os.path.split(path)
        parent = os.path.basename(parent)
        path = os.path.join(parent, leaf)
    else:
        path = v.name() or str(v.buffer_id())
        leaf = v.name() or 'untitled'

    status = [] 
    if not v.file_name():
        status.append("t")
    if v.is_dirty():
        status.append("*")
    if v.is_read_only():
        status.append("r")
    
    if status:
        leaf += ' (%s)' % ', '.join(status)
    return [leaf, path]


def get_region_by_range(view, text_range, split_visual=False):
    # xxx move this further down into the range parsing?
    global GLOBAL_RANGES
    if GLOBAL_RANGES:
        rv = GLOBAL_RANGES[:]
        GLOBAL_RANGES = []
        return rv
        
    if text_range.replace(' ', '') == "'<,'>":
        if not split_visual:
            return list(view.sel())
        else:
            rv = []
            for r in list(view.sel()):
                rv.extend(view.split_by_newlines(r))
            return rv

    a, b = ex_range.calculate_range(view, text_range)
    r = sublime.Region(view.text_point(a - 1, 0),
                        view.full_line(
                            view.text_point(b - 1, 0)).end())    
    return view.split_by_newlines(r)


def calculate_address(view, text_range):
    """calculates single line address based on a range.
    """
    # doublecheck allowed ranges with vim
    # xxx strip in the parsing phase instead
    a, b = ex_range.calculate_range(view, text_range.strip())
    address = (max(a, b) if all((a, b)) else (a or b)) or 0
    return address - 1


def get_oem_cp():
    codepage = ctypes.windll.kernel32.GetOEMCP()
    return str(codepage)


def get_startup_info():
    # Hide the child process window.
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def ensure_line_block(view, r):
    """returns a string containing lines terminated by a newline character.
    """
    if view.substr(r).endswith('\n'):
        r = sublime.Region(r.begin(), r.end() - 1)
    line_block = view.substr(view.line(r)) + '\n'

    return line_block


class ExGoto(sublime_plugin.TextCommand):
    def run(self, edit, range=''):
        assert range, 'Range required.'
        a, b = ex_range.calculate_range(self.view, range, is_only_range=True)
        target = (max(a, b) if all((a, b)) else (a or b)) or 0
        self.view.run_command('vi_goto_line', {'repeat': target})
        self.view.show(self.view.sel()[0])


class ExShellOut(sublime_plugin.TextCommand):
    def run(self, edit, range='', shell_cmd=''):
        if range:
            if sublime.platform() == 'windows':
                for r in get_region_by_range(self.view, range):
                    rv = filter_region(self.view.substr(r), shell_cmd)
                    self.view.replace(edit, r, rv)
                return
            elif sublime.platform() == 'linux':
                for s in self.view.sel():
                    shell = os.path.expandvars("$SHELL")
                    p = subprocess.Popen([shell, '-c', shell_cmd],
                                                        stdout=subprocess.PIPE)
                    self.view.replace(edit, s, p.communicate()[0][:-1])
                return
            else:
                handle_not_implemented()
        elif sublime.platform() == 'linux':
            term = os.path.expandvars("$COLORTERM") or \
                                                    os.path.expandvars("$TERM")
            subprocess.Popen([term, '-e',
                    "bash -c \"%s; read -p 'Press RETURN to exit.'\"" %
                                                            shell_cmd]).wait()
            return
        elif sublime.platform() == 'windows':
            subprocess.Popen(['cmd.exe', '/c', shell_cmd + '&& pause']).wait()
            return 
        else:
            handle_not_implemented()


class ExShell(sublime_plugin.TextCommand):
    """Ex command(s): :shell

    Opens a shell at the current view's directory. Sublime Text keeps a virtual
    current directory that most of the time will be out of sync with the actual
    current directory. The virtual current directory is always set to the
    current view's directory, but it isn't accessible through the API.
    """
    def open_shell(self, command):
        view_dir = os.path.dirname(self.view.file_name())
        return subprocess.Popen(command, cwd=view_dir)
        
    def run(self, edit):
        if sublime.platform() == 'linux':
            term = os.path.expandvars('$COLORTERM') or \
                                                    os.path.expandvars('$TERM')
            self.open_shell([term, '-e', 'bash']).wait()
        elif sublime.platform() == 'windows':
            self.open_shell(['cmd.exe', '/k']).wait()
        else:
            # XXX OSX (make check explicit)
            handle_not_implemented()


class ExReadShellOut(sublime_plugin.TextCommand):
    def run(self, edit, range='', name='', plusplus_args='', forced=False):
        target_line = self.view.line(self.view.sel()[0].begin())
        if range:
            range = max(ex_range.calculate_range(self.view, range))
            target_line = self.view.line(self.view.text_point(range, 0))
        target_point = min(target_line.b + 1, self.view.size())

        # cheat a little bit to get the parsing right:
        #   - forced == True means we need to execute a command
        if forced:
            if sublime.platform() == 'linux':
                for s in self.view.sel():
                    shell = os.path.expandvars("$SHELL")
                    p = subprocess.Popen([shell, '-c', name],
                                                        stdout=subprocess.PIPE)
                    self.view.insert(edit, s.begin(), p.communicate()[0][:-1])
            elif sublime.platform() == 'windows':
                for s in self.view.sel():
                    p = subprocess.Popen(['cmd.exe', '/C', name],
                                            stdout=subprocess.PIPE,
                                            startupinfo=get_startup_info()
                                            )
                    cp = 'cp' + get_oem_cp()
                    rv = p.communicate()[0].decode(cp)[:-2].strip()
                    self.view.insert(edit, s.begin(), rv)
            else:
                handle_not_implemented()
        # Read a file into the current view.
        else:
            # Read the current buffer's contents and insert below current line.
            if not name:
                new_contents = self.view.substr(
                                        sublime.Region(0, self.view.size()))
                if self.view.substr(target_line.b) != '\n':
                    new_contents = '\n' + new_contents
                self.view.insert(edit, target_point, new_contents)
                return
            # xxx read file "name"
            # we need proper filesystem autocompletion here
            else:
                handle_not_implemented()
                return


class ExPromptSelectOpenFile(sublime_plugin.TextCommand):
    """Ex command(s): :ls, :files

    Shows a quick panel listing the open files only. Provides concise
    information about the buffers's state: 'transient', 'unsaved'.
    """
    def run(self, edit):
        self.file_names = [gather_buffer_info(v)
                                        for v in self.view.window().views()]
        self.view.window().show_quick_panel(self.file_names, self.on_done)

    def on_done(self, idx):
        if idx == -1: return
        sought_fname = self.file_names[idx]
        for v in self.view.window().views():
            if v.file_name() and v.file_name().endswith(sought_fname[1]):
                self.view.window().focus_view(v)
            # xxx Base all checks on buffer id?
            elif sought_fname[1].isdigit() and \
                                        v.buffer_id() == int(sought_fname[1]):
                self.view.window().focus_view(v)


class ExMap(sublime_plugin.TextCommand):
    # do at least something moderately useful: open the user's .sublime-keymap
    # file
    def run(self, edit):
        if sublime.platform() == 'windows':
            plat = 'Windows'
        elif sublime.platform() == 'linux':
            plat = 'Linux'
        else:
            plat = 'OSX'
        self.view.window().run_command('open_file', {'file':
                                        '${packages}/User/Default (%s).sublime-keymap' % plat})        


class ExAbbreviate(sublime_plugin.TextCommand):
    # for them moment, just open a completions file.
    def run(self, edit):
        abbreviations_file = os.path.join(
                                    sublime.packages_path(),
                                    'User/Vintage Abbreviations.sublime-completions'
                                    )
        if not os.path.exists(abbreviations_file):
            with open(abbreviations_file, 'w'):
                pass
        
        self.view.window().run_command('open_file',
                                            {'file': abbreviations_file})


class ExPrintWorkingDir(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime.status_message(os.getcwd())


class ExWriteFile(sublime_plugin.TextCommand):
    def run(self, edit,
                range=None,
                forced=False,
                file_name='',
                plusplus_args='',
                operator='',
                target_redirect='',
                subcmd=''):
        
        if file_name and target_redirect:
            sublime.status_message('VintageEx: Too many arguments.')
            return

        appending = operator == '>>'
        content = get_region_by_range(self.view, range)[0] if range else \
                        sublime.Region(0, self.view.size())
        
        if target_redirect or file_name:
            target = self.view.window().new_file()
            target.set_name(target_redirect or file_name)
        else:
            target = self.view

        start = 0 if not appending else target.size()
        prefix = '\n' if appending and target.size() > 0 else ''
        
        if appending or target_redirect or file_name:
            target.insert(edit, start, prefix + self.view.substr(content))
        elif range:
            text = self.view.substr(content) 
            self.view.insert(edit, 0, text)
            self.view.replace(edit, sublime.Region(len(text), 
                                        self.view.size()), '')
        else:
            if self.view.is_dirty():
                self.view.run_command('save')


class ExWriteAll(sublime_plugin.TextCommand):
    def run(self, edit, forced=False):
        for v in self.view.window().views():
            if v.is_dirty():
                v.run_command('save')


class ExNewFile(sublime_plugin.TextCommand):
    def run(self, edit, forced=False):
        self.view.window().run_command('new_file')


class ExAscii(sublime_plugin.TextCommand):
    def run(self, edit, range='', forced=False):
        handle_not_implemented()


class ExFile(sublime_plugin.TextCommand):
    def run(self, edit, forced=False):
        # xxx figure out what the right params are. vim's help seems to be
        # wrong
        if self.view.file_name():
            fname = self.view.file_name()
        else:
            fname = 'untitled' 
        
        attrs = ''
        if self.view.is_read_only():
            attrs = 'readonly' 
        
        if self.view.is_scratch():
            attrs = 'modified'
        
        lines = 'no lines in the buffer'
        if self.view.rowcol(self.view.size())[0]:
            lines = self.view.rowcol(self.view.size())[0] + 1
        
        # fixme: doesn't calculate the buffer's % correctly
        if not isinstance(lines, basestring):
            vr = self.view.visible_region()
            start_row, end_row = self.view.rowcol(vr.begin())[0], \
                                              self.view.rowcol(vr.end())[0]
            mid = (start_row + end_row + 2) / 2
            percent = float(mid) / lines * 100.0
        
        msg = fname
        if attrs:
            msg += " [%s]" % attrs
        if isinstance(lines, basestring):
            msg += " -- %s --"  % lines
        else:
            msg += " %d line(s) --%d%%--" % (lines, int(percent))
        
        sublime.status_message('VintageEx: %s' % msg)


class ExMove(sublime_plugin.TextCommand):
    def run(self, edit, range='.', forced=False, address=''):
        assert range, "Need a range."
        if int(address) != 0:
            address = calculate_address(self.view, address)
        else:
            address = 0

        line_block = [] 
        for r in get_region_by_range(self.view, range):
            ss = ensure_line_block(self.view, r)
            line_block.append(ss)

        offset = 0
        for r in reversed(get_region_by_range(self.view,
                                                range, split_visual=True)):
            if self.view.rowcol(r.begin())[0] + 1 < address:
                offset +=  1
            self.view.erase(edit, self.view.full_line(r))

        text = ''.join(line_block)
        if address != 0:
            dest = self.view.line(self.view.text_point(
                                                address - offset, 0)).end() + 1
        else:
            dest = 0

        if dest > self.view.size():
            dest = self.view.size()
            text = '\n' + text[:-1]
        self.view.insert(edit, dest, text)

        self.view.sel().clear()
        cursor_dest = self.view.line(dest + len(text) - 1).begin()
        self.view.sel().add(sublime.Region(cursor_dest, cursor_dest))


class ExCopy(sublime_plugin.TextCommand):
    def run(self, edit, range='.', forced=False, address=''):
        assert range, "Need a range."
        if int(address) != 0:
            address = calculate_address(self.view, address)
        else:
            address = 0

        line_block = [] 
        for r in get_region_by_range(self.view, range):
            ss = ensure_line_block(self.view, r)
            line_block.append(ss)
        
        text = ''.join(line_block)
        if address != 0:
            dest = self.view.line(self.view.text_point(address, 0)).end() + 1
        else:
            dest = address
        if dest > self.view.size():
            dest = self.view.size()
            text = '\n' + text[:-1]
        self.view.insert(edit, dest, text)

        self.view.sel().clear()
        cursor_dest = self.view.line(dest + len(text) - 1).begin()
        self.view.sel().add(sublime.Region(cursor_dest, cursor_dest))


class ExSubstitute(sublime_plugin.TextCommand):
    last_pattern = None
    last_flags = ''
    parts_rgex = re.compile(r"([:/])(.*?)(\1)(.*?)(\1)([a-zA-Z]+)?( \d+)?")
    def run(self, edit, range='.', pattern=''):
        range = range or '.'

        # we either accept a full pattern plus flags and count arg
        # ... or ...
        # simply a command in the following forms:
        #   :s
        #   :s gi
        #   :s gi 10
        #   :s 10
        try:
            sep, left, _, right, _, flags, count = \
                            ExSubstitute.parts_rgex.search(pattern).groups()
            ExSubstitute.last_pattern = (left, right)
            ExSubstitute.last_flags = flags
        except AttributeError:
            if not ExSubstitute.last_pattern:
                sublime.status_message("VintageEx: No pattern available.")
                return
            left, _, right = pattern.strip().partition(' ')
            flags, count = '', None
            if left and left.strip().isalpha():
                flags = left
                if right and right.isdigit():
                    count = int(right)
                elif right:
                    sublime.status_message('VintageEx: Bad pattern.') 
                    return
            elif left and left.strip().isdigit():
                count = int(left)
            
            if flags or count:
                pattern = ''
        
        if not pattern:
            left, right = ExSubstitute.last_pattern

        re_flags = 0
        re_flags |= re.IGNORECASE if (flags and 'i' in flags) else 0
        left = re.compile(left, flags=re_flags)

        if count and range == '.':
            range = '.,.+%d' % int(count)
        elif count:
            a, b = ex_range.calculate_range(self.view, range)
            if not a and b:
                b = max(a, b)
            range = "%d,%d+%d" % (b, b, int(count))

        target_region = get_region_by_range(self.view, range)
        replace_count = 0 if (flags and 'g' in flags) else 1
        for r in reversed(target_region):
            # be explicit about replacing the line, because we might be looking
            # at a Ctrl+D sequence of regions (not spanning a whole line)
            line_text = self.view.substr(self.view.line(r))
            rv = re.sub(left, right, line_text, count=replace_count)
            self.view.replace(edit, self.view.line(r), rv)


class ExDelete(sublime_plugin.TextCommand):
    def run(self, edit, range='.', register='', count=''):
        # xxx somewhat different to vim's behavior
        rs = get_region_by_range(self.view, range)
        self.view.sel().clear()

        to_store = []
        for r in rs:
            self.view.sel().add(r)
            if register:
                to_store.append(self.view.substr(self.view.full_line(r)))
        
        if register:
            text = ''.join(to_store)
            # needed for lines without a newline character
            if not text.endswith('\n'):
                text = text + '\n'
            set_register(text, register)
        
        self.view.run_command('split_selection_into_lines')
        self.view.run_command('run_macro_file',
                        {'file': 'Packages/Default/Delete Line.sublime-macro'})


class ExGlobal(sublime_plugin.TextCommand):
    def run(self, edit, range='%', forced=False, pattern=''):
        _, global_pattern, subcmd = pattern.split(pattern[0], 2)
        subcmd = subcmd or 'print'

        rs = get_region_by_range(self.view, range)

        for r in rs:
            match = re.search(global_pattern, self.view.substr(r))
            if (match and not forced) or (not match and forced):
                GLOBAL_RANGES.append(r)

        self.view.run_command('vi_colon_input',
                                    {'cmd_line': ':' + 
                                        str(self.view.rowcol(r.a)[0] + 1) +
                                                                    subcmd})

                                                                    
class ExPrint(sublime_plugin.TextCommand):
    def run(self, edit, range='.', count='1', flags=''):
        if not count.isdigit():
            flags, count = count, ''
        rs = get_region_by_range(self.view, range)
        to_display = []
        for r in rs:
            for line in self.view.lines(r):
                text = self.view.substr(line)
                if '#' in flags:
                    row = self.view.rowcol(line.begin())[0] + 1
                else:
                    row = ''
                to_display.append((text, row))

        v = self.view.window().new_file()
        v.set_scratch(True)
        if 'l' in flags:
            v.settings().set('draw_white_space', 'all')
        for t, r in to_display:
            v.insert(edit, v.size(), (str(r) + ' ' + t + '\n').lstrip())
