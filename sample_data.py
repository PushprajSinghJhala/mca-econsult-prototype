# sample_data.py
from app import create_app
from models import db, User, Comment
from sentiment import analyze_sentiment

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    u = User(name="Parag Student", email="parag@example.com", pan="ABCDE1234F")
    db.session.add(u)
    comments = [
        ("Sakshi","sakshi@x.com","ABCDE1234F","I support this amendment, it is clear and helpful."),
        ("Ravi","","","This will create a problem for small companies and is difficult to comply."),
        ("Asha","asha@x.com","","Neutral comment with no clear opinion.")
    ]
    for name,email,pan,text in comments:
        label,score = analyze_sentiment(text)
        comment = Comment(name=name,email=email,pan_masked=("****"+pan[-4:] if pan else None), text=text, sentiment=label, score=score, user=u if pan==u.pan else None)
        db.session.add(comment)
    db.session.commit()
    print("Seeded sample data")
