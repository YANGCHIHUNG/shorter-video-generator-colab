from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download")
def download():
    return render_template("download.html")

@app.route("/documentation")
def documentation():
    return render_template("documentation.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
