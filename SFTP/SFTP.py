import sublime
import traceback
import os
import sys
import time
import imp

settings = sublime.load_settings('SFTP.sublime-settings')

if sublime.platform() == 'linux' and settings.get('linux_enable_ssl'):
    print 'SFTP: enabling custom linux ssl module'
    arch_lib_path = os.path.join(sublime.packages_path(), 'SFTP', 'lib',
        'linux-' + sublime.arch())
    for ssl_ver in ['0.9.8', '1.0.0', '10']:
        lib_path = os.path.join(arch_lib_path, 'libssl-' + ssl_ver)
        try:
            m_info = imp.find_module('_ssl', [lib_path])
            m = imp.load_module('_ssl', *m_info)
            print 'SFTP: successfully loaded _ssl module for libssl.so.%s' % ssl_ver
            break
        except (ImportError) as (e):
            print 'SFTP: _ssl module import error - ' + str(e)
    if '_ssl' in sys.modules:
        plat_lib_path = os.path.join(sublime.packages_path(), 'SFTP', 'lib',
            'linux')
        try:
            m_info = imp.find_module('ssl', [plat_lib_path])
            m = imp.load_module('ssl', *m_info)
        except (ImportError) as (e):
            print 'SFTP: ssl module import error - ' + str(e)

reload_mods = []
for mod in sys.modules:
    if (mod[0:5] == 'sftp.' or mod == 'sftp') and sys.modules[mod] != None:
        reload_mods.append(mod)
mods_load_order = [
    'sftp',
    'sftp.times',
    'sftp.views',
    'sftp.paths',
    'sftp.debug',
    'sftp.errors',
    'sftp.threads',
    'sftp.secure_input',
    'sftp.proc',
    'sftp.vcs',
    'sftp.config',
    'sftp.panel_printer',
    'sftp.file_transfer',
    'sftp.ftplib2',
    'sftp.ftp_transport',
    'sftp.ftps_transport',
    'sftp.sftp_transport',
    'sftp.commands',
    'sftp.listeners'
]
for mod in mods_load_order:
    if mod in reload_mods:
        reload(sys.modules[mod])

from sftp.commands import (SftpShowPanelCommand, SftpCreateServerCommand,
    SftpBrowseServerCommand, SftpLastServerCommand, SftpEditServerCommand,
    SftpDeleteServerCommand, SftpBrowseCommand, SftpUploadFileCommand,
    SftpMonitorFileCommand, SftpUploadOpenFilesCommand,
    SftpDiffRemoteFileCommand, SftpRenameLocalAndRemotePathsCommand,
    SftpDeleteRemotePathCommand, SftpDownloadFileCommand,
    SftpUploadFolderCommand, SftpSyncUpCommand, SftpSyncDownCommand,
    SftpSyncBothCommand, SftpDownloadFolderCommand, SftpVcsChangedFilesCommand,
    SftpCancelUploadCommand, SftpEditConfigCommand, SftpCreateConfigCommand,
    SftpCreateSubConfigCommand, SftpThread)
from sftp.listeners import (SftpCloseListener, SftpLoadListener,
    SftpFocusListener, SftpAutoUploadListener, SftpAutoConnectListener)

import sftp.debug
import sftp.paths
import sftp.times

sftp.debug.set_debug(settings.get('debug', False))


# Override default uncaught exception handler
def uncaught_except(type, value, tb):
    message = ''.join(traceback.format_exception(type, value, tb))

    if message.find('/sftp/') != -1 or message.find('\\sftp\\') != -1:
        def append_log():
            log_file_path = os.path.join(sublime.packages_path(), 'User',
                'SFTP.errors.log')
            send_log_path = log_file_path
            timestamp = sftp.times.timestamp_to_string(time.time(),
                    '%Y-%m-%d %H:%M:%S\n')
            with open(log_file_path, 'a') as f:
                f.write(timestamp)
                f.write(message)
            if sftp.debug.get_debug() and sftp.debug.get_debug_log_file():
                send_log_path = sftp.debug.get_debug_log_file()
                sftp.debug.debug_print(message)
            sublime.error_message(('%s: An unexpected error occurred, ' +
                'please send the file %s to support@wbond.net') % ('SFTP',
                send_log_path))
            sublime.active_window().run_command('open_file',
                {'file': sftp.paths.fix_windows_path(send_log_path)})
        sublime.set_timeout(append_log, 10)

    sys.__excepthook__(type, value, tb)
if sys.excepthook.__name__ != 'uncaught_except':
    sys.excepthook = uncaught_except


def unload_handler():
    # Kill all connections
    SftpThread.cleanup()

    # Reset the exception handler
    if sys.excepthook.__name__ == 'uncaught_except':
        sys.excepthook = sys.__excepthook__
