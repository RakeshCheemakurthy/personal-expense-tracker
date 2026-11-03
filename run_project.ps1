# Navigate to the project folder
Set-Location $PSScriptRoot

# Create virtual environment if it does not exist
if (!(Test-Path ".venv")) {
    python -m venv .venv
}

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Install required packages
python -m pip install -r requirements.txt

# Run the application
python app.py
