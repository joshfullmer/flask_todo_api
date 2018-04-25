from flask import Flask, g, jsonify, render_template

import config

app = Flask(__name__)


@app.route('/')
def my_todos():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)