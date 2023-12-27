import subprocess as sp

class Extension:
    def __init__(self, api):
        self.api = api

    def run(self):
        reqs = sp.check_output(['pip', 'freeze'])
        if not "python-lsp-server".encode() in reqs:
            try:
                sp.check_call(['pip', 'install', 'python-lsp-server'])
            except sp.CalledProcessError:
                self.api.notifications.warning("Python extension requires python-lsp-server to be installed")
        self.api.register_langserver('Python', 'pylsp')
        
