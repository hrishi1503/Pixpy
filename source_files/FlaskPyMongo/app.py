from flask import Flask, request, url_for, render_template, redirect
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/errors"
mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/trial", methods=["POST","GET"])
def trial():
    if request.method == "POST":
        errorcode = request.form["Code"]
        return redirect(url_for("errfind", errcode=errorcode))
    else:
        return render_template("info.html")

@app.route("/<errcode>")
def errfind(errcode):
    return render_template("result.html")

if __name__ == "__main__":
    app.run(debug=True)