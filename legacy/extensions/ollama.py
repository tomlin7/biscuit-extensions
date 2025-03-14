from __future__ import annotations

import webbrowser

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import subprocess
import typing

try:
    import ollama
except ImportError:
    try:
        subprocess.run(["pip", "install", "ollama"], check=True)
        import ollama
    except Exception as e:
        ollama = None

from biscuit.common.chat import ChatModelInterface
from biscuit.extensions import Extension

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


OLLAMA_HOME = "https://ollama.com/"
TINYLLAMA = "tinyllama:latest"
PYPI_COMMAND = "pip install ollama"


class OllamaChatModel(ChatModelInterface):
    model_name: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.prompt = """You are an AI assistant named Bikkis. You assist user in writing code, documents, and more.
            Keep your messages very short and to the point, because user can't read long messages.
            
            Now respond to following message: """

    def start_chat(self): ...
    def send_message(self, message: str):
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": f"{self.prompt} {message}"}],
        )
        return response["message"]["content"]


class Ollama(Extension):
    """Ollama extension for Biscuit (author: @tomlin7)

    Contributes:
    - Registers ollama as provider for AI chat
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)

    def install(self) -> None:
        if not ollama:
            return self.api.notifications.info(
                "Ollama-python is not installed. Install it to use this extension.",
                actions=[
                    (
                        "Install",
                        lambda: self.api.terminalmanager.run_command(
                            "pip install ollama"
                        ),
                    ),
                ],
            )

        try:
            response = ollama.list()
            if not response:
                return self.prompt_install_tiny()

            for model in response["models"]:
                name = model["name"]
                if not name:
                    continue

                subclass = self.create_model_class(name)
                self.api.assistant.register_provider(name, subclass)

        except Exception as e:
            self.api.notifications.info(
                "It seems Ollama is not installed. Install it to use this extension.",
                actions=[("Open link", lambda: webbrowser.open(OLLAMA_HOME))],
            )
            return self.api.logger.error(f"Failed to fetch models from Ollama: {e}")

    def create_model_class(self, model_name: str) -> OllamaChatModel:
        return type(
            "Ollama_{}".format(model_name.replace(":", "_")),
            (OllamaChatModel,),
            {"model_name": model_name},
        )

    def prompt_install_tiny(self) -> None:
        self.api.notifications.info(
            "No models found. Install tinyllama to get started?",
            actions=[
                (
                    "Yes",
                    lambda: ollama.pull(TINYLLAMA),
                ),
            ],
        )


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("ollama", Ollama(api))


# 5. Start customizing your extension!
