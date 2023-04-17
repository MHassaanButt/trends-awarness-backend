# coding: utf8
# from ssl import VERIFY_ALLOW_PROXY_CERTS


from urllib import response
from flask import Flask, render_template, redirect, url_for, jsonify, request, make_response, send_file

# from flask import Flask, flash, jsonify, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from scrape import *
from sentiments import Sentimment_Intensity_Analyzer
from multi_tweets_extraction import *
from visulization import *
import subprocess
from datetime import datetime
import json, requests, glob, shutil,os
from pathlib import Path
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/hassaan/Documents/user_profiling_for_social_media/twitter_app/database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

globalDic = {}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_table():
    db.create_all()


class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(
        message='Invalid email'), Length(max=50)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(
        message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])


class ScrapeForm(FlaskForm):
    since = StringField('since', validators=[InputRequired()])
    until = StringField('until')
    words = StringField('words')
    hashtag = StringField('hashtag')
    from_account = StringField('from_account')
    mention_account = StringField('mention_account')
    limit = StringField('limit')

    interval = StringField('interval')
    language = StringField('language')
    display_type = StringField('display_type')


@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/analytics')
def analytics():
    return render_template('analytics.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.get_json()
    password = data['password']
    user = User.query.filter_by(email=data['email']).first()
    
    if user:
        if user.password== password:
            response = {'message': 'Login successful'}
            return jsonify(response)
        else:
            response = {'message': 'Invalid password'}
            return jsonify(response) 
    response = {'message': 'Invalid emal'}
    return jsonify(response)      



@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    password = data['password']
    new_user = User(
        username=data['firstName'] + ' ' + data['lastName'],
        email=data['email'],
        password=password
    )
    db.session.add(new_user)
    db.session.commit()

    response = {'message': 'Signup successful'}
    return jsonify(response)

def convert_to_dict(lst):
    if not lst:
        return {}
    elif len(lst) == 1:
        return lst[0]
    else:
        return {i: lst[i] for i in range(len(lst))}

def handle_non_serializable(obj):
    if isinstance(obj, spacy.tokens.Span):
        return {'start': obj.start, 'end': obj.end}
    raise TypeError('Object of type %s is not JSON serializable' % type(obj))



@app.route('/tweet_scrape', methods=['GET', 'POST'])
def scaper():
    form = ScrapeForm()
    since = str(form.data.get('since'))
    until = str(form.data.get('until'))
    words = form.data.get('words')
    hashtag = form.data.get('hashtag')
    from_account = str(form.data.get('from_account'))
    mention_account = str(form.data.get('mention_account'))
    limit = int(form.data.get('limit'))
    interval = int(form.data.get('interval'))
    language = str(form.data.get('language'))
    display_type = str(form.data.get('display_type'))

    tweets = scrape(hashtag=hashtag, words=words, since=since, until=until, interval=interval, headless=True, limit=limit)

    mlt = Multi_Tweets_Extraction()
    sentiments = Sentimment_Intensity_Analyzer()
    mlt_df = mlt.multi_tweets(tweets)
    df = pd.DataFrame(mlt_df)
    pre_clean_df = sentiments.pre_senti(df)
    temp = pre_clean_df.to_dict(orient='records')
    original_dict = convert_to_dict(temp)

    def clean_tweet_text(text):
        # Remove mentions
        text = re.sub(r'@[A-Za-z0-9_]+', '', text)
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove non-alphanumeric characters
        text = re.sub(r'\W+', ' ', text)
        # Convert to lowercase
        text = text.lower()
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    cleaned_dict = {}
    tweet_id = 0
    for tweet_data in original_dict.values():
        cleaned_tweet_data = tweet_data.copy()
        cleaned_tweet_data['text_clean'] = clean_tweet_text(tweet_data['orginal_tweet'])
        cleaned_dict[tweet_id] = cleaned_tweet_data
        tweet_id += 1

    def analyze_sentiment(cleaned_dict):
        analyzer = SentimentIntensityAnalyzer()
        final_tweets = []
        for _, tweet in cleaned_dict.items():
            text = tweet["text_clean"]
            sentiment_scores = analyzer.polarity_scores(text)
            compound_score = sentiment_scores["compound"]
            threshold = 0.05
            sentiment = ""
            if compound_score > threshold:
                sentiment = "positive"
            elif compound_score < -threshold:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            tweet_data = {
                "tweet_id": tweet["tweet_id"],
                "UserScreenName": tweet["UserScreenName"],
                "UserName": tweet["UserName"],
                "orginal_tweet": tweet["orginal_tweet"],
                "Likes": tweet["Likes"],
                "Retweets": tweet["Retweets"],
                "Image_link": tweet["Image_link"][0] if tweet["Image_link"] else None,
                "text_clean": tweet["text_clean"],
                "sentiment": sentiment
            }
            final_tweets.append(tweet_data)
        return json.dumps(final_tweets)

    final_tweets = analyze_sentiment(cleaned_dict)
    return final_tweets

    # print(cleaned_dict)


    # return jsonify(json_data)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
