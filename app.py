# app.py
import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Comment
from sentiment import analyze_sentiment
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-me'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Routes
    @app.route("/")
    def index():
        total = Comment.query.count()
        users = User.query.count()
        recent = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
        return render_template("index.html", total=total, users=users, recent=recent)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            pan = request.form.get("pan")
            if not (name and email and pan):
                flash("Please fill all fields", "danger")
                return redirect(url_for('register'))
            # simple uniqueness check
            existing = User.query.filter_by(pan=pan).first()
            if existing:
                flash("PAN already registered. You can submit comments directly.", "info")
                return redirect(url_for("index"))
            user = User(name=name, email=email, pan=pan)
            db.session.add(user)
            db.session.commit()
            flash("Registered successfully!", "success")
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.route("/submit-comment", methods=["GET", "POST"])
    def submit_comment():
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            pan = request.form.get("pan")
            text = request.form.get("text")
            if not text or not name:
                flash("Please include your name and comment text", "danger")
                return redirect(url_for("submit_comment"))

            # try find user
            user = None
            pan_masked = None
            if pan:
                user = User.query.filter_by(pan=pan).first()
                if user:
                    pan_masked = user.masked_pan()
                else:
                    pan_masked = "****" + pan[-4:] if len(pan) > 4 else "****"

            sentiment_label, score = analyze_sentiment(text)
            comment = Comment(
                user=user,
                name=name,
                email=email,
                pan_masked=pan_masked,
                text=text,
                sentiment=sentiment_label,
                score=score
            )
            db.session.add(comment)
            db.session.commit()
            flash(f"Submitted! Sentiment: {sentiment_label}", "success")
            return redirect(url_for("comments"))

        return render_template("submit_comment.html")

    @app.route("/upload-csv", methods=["GET", "POST"])
    def upload_csv():
        """
        CSV format expected: name,email,pan,comment
        """
        if request.method == "POST":
            file = request.files.get("file")
            if not file:
                flash("Please upload a CSV file", "danger")
                return redirect(url_for("upload_csv"))
            stream = file.stream.read().decode("utf-8").splitlines()
            reader = csv.DictReader(stream)
            count = 0
            for row in reader:
                name = row.get("name") or "Anonymous"
                email = row.get("email")
                pan = row.get("pan")
                text = row.get("comment") or row.get("text") or ""
                if not text.strip():
                    continue
                # map user if exists
                user = None
                pan_masked = None
                if pan:
                    user = User.query.filter_by(pan=pan).first()
                    if user:
                        pan_masked = user.masked_pan()
                    else:
                        pan_masked = "****" + pan[-4:] if len(pan) > 4 else "****"

                label, score = analyze_sentiment(text)
                comment = Comment(
                    user=user,
                    name=name,
                    email=email,
                    pan_masked=pan_masked,
                    text=text,
                    sentiment=label,
                    score=score
                )
                db.session.add(comment)
                count += 1
            db.session.commit()
            flash(f"Imported {count} comments", "success")
            return redirect(url_for("dashboard"))
        return render_template("upload_csv.html")

    @app.route("/comments")
    def comments():
        page = int(request.args.get("page", 1))
        per = 20
        items = Comment.query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
        return render_template("comments.html", comments=items.items, pagination=items)

    @app.route("/dashboard")
    def dashboard():
        # build summary stats
        total = Comment.query.count()
        pos = Comment.query.filter_by(sentiment="Positive").count()
        neg = Comment.query.filter_by(sentiment="Negative").count()
        neu = Comment.query.filter_by(sentiment="Neutral").count()
        recent = Comment.query.order_by(Comment.created_at.desc()).limit(10).all()
        # topics placeholder: top words
        return render_template("dashboard.html", total=total, pos=pos, neg=neg, neu=neu, recent=recent)

    @app.route("/api/sentiment-data")
    def sentiment_data_api():
        pos = Comment.query.filter_by(sentiment="Positive").count()
        neg = Comment.query.filter_by(sentiment="Negative").count()
        neu = Comment.query.filter_by(sentiment="Neutral").count()
        return jsonify({"positive": pos, "negative": neg, "neutral": neu})

    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",port=port)
