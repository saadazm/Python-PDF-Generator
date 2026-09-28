"""CLI entry point kept for backward compatibility.

The rendering logic now lives in pdf_engine.py so it can be shared with
the API service (api/main.py). Running this file directly reproduces the
original script's output.
"""
import os
from pdf_engine import generate_pdf

script_dir = os.path.dirname(os.path.abspath(__file__))
generated_pdf_path = os.path.join(script_dir, "generated.pdf")

if __name__ == "__main__":
    generate_pdf(generated_pdf_path, [
        "Start....... ",
    ])
    print(f"Generated PDF saved at: {generated_pdf_path}")
