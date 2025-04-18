# PinkBird

A simplified Twitter clone built with Flask and Tailwind CSS.

## Setup

### Database Setup

1. Make sure MySQL is installed and running
2. Initialize the database:
   ```
   mysql -u root -p < setup.sql
   ```
   
   Note: If your MySQL credentials are different, update them in `db.py`

### Python Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

### Tailwind CSS Setup

1. Install Node.js dependencies:
   ```
   npm install
   ```

2. Build the CSS:
   ```
   npm run build-css
   ```

## Running the Application

1. Start the Flask server:
   ```
   python main.py
   ```

2. Open your browser and go to:
   ```
   http://localhost:5000
   ```

## Development

During development, keep the Tailwind CSS build process running in a separate terminal:
```
npm run build-css
```

This will watch for changes to your CSS and HTML files and automatically rebuild the CSS file. 