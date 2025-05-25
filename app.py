from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)

# Get bot username for the template
bot_username = os.environ.get("BOT_USERNAME", "YourBotUsername")

@app.route('/')
def index():
    """Main page that redirects to the bot."""
    return render_template('index.html', bot_username=bot_username)

@app.route('/health')
def health():
    """Health check endpoint for deployment platforms."""
    return {"status": "healthy", "service": "AI ESCROW BOT"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)