from __future__ import annotations

__version__ = '0.0.1'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])


import subprocess as sp
import typing

if typing.TYPE_CHECKING:
    from biscuit import ExtensionsAPI

class Extension:
    """JavaScript and TypeScript extension for Biscuit (author: @billyeatcookies)
    
    Extension will automatically install typescript-language-server if not installed.
    
    Contributes:
    - language server configuration for Javascript & TypeScript (typescript-language-server)
    """
    
    def __init__(self, api: ExtensionsAPI):
        self.api = api

    def run(self):
        try:
            sp.Popen(['npm', 'install', '-g', 'typescript-language-server'], shell=True)
            sp.Popen(['npm', 'install', '-g', 'typescript'], shell=True)
        except sp.CalledProcessError:
            self.api.notifications.warning("Ensure you have npm & nodejs installed and in your PATH.")
        self.api.register_langserver('JavaScript', 'typescript-language-server --stdio')
        self.api.register_langserver('TypeScript', 'typescript-language-server --stdio')
