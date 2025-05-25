from flask import Flask, render_template
import os

app = Flask(__name__)

# Get bot username for the template
bot_username = os.environ.get("BOT_USERNAME", "YourBotUsername")

@app.route('/')
def index():
    """Main page that displays information about the bot."""
    return render_template('index.html', bot_username=bot_username)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)