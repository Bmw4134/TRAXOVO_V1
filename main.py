from app import app  # noqa: F401
from cli import register_cli_commands

# Register CLI commands
register_cli_commands(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
