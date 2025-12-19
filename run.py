# run.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True allows auto-reload and shows errors in browser
    app.run(host="127.0.0.1", port=5000, debug=True)
