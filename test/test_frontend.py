import os, sys

# src/ in den Python-Pfad aufnehmen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from myapp.frontend.gradio_app import demo

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
