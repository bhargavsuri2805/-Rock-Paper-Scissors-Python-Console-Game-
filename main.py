# Import the Flask app instance from app.py
from app import app

# Entry point that will be used to run the application
if __name__ == "__main__":
    # Start the development server on host 0.0.0.0 and port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
