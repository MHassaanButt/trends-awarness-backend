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


app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
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
    print("In login form")
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
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


@app.route('/', methods=['GET', 'POST'])
def login():
    print('In login')
    form = LoginForm()

    if form.validate_on_submit():
        print('validate_on_submit()')
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            print('in user')
            if check_password_hash(user.password, form.password.data):
                print('in check password hash')
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
            else:
                print("Invalid password")
        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method='sha256')
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/tweet_scrape', methods=['GET', 'POST'])
def scaper():

    form = ScrapeForm()
    since = form.data.get('since')
    since = str(since)
    until = form.data.get('until')
    until = str(until)
    words = form.data.get('words')
    hashtag = form.data.get('hashtag')
    from_account = form.data.get('from_account')
    from_account = str(from_account)
    mention_account = form.data.get('mention_account')
    mention_account = str(mention_account)
    limit = form.data.get('limit')
    limit = int(limit)
    interval = form.data.get('interval')
    interval = int(interval)
    language = form.data.get('language')
    language = str(language)
    display_type = form.data.get('display_type')
    display_type = str(display_type)

    ############################### JUST FOR TESTING ##################################
    """ df=pd.read_csv('outputs/hashtag_tweets_new.csv')
    dict=df.to_dict()
    return render_template('results.html',data=dict) """
    ############################## JUST FOR TESTING####################################
    tweets = scrape(hashtag=hashtag, words=words, since=since, until=until, from_account=from_account,
                    to_account=None, mention_account=mention_account, interval=interval, headless=True, display_type=display_type, save_images=False,
                    proxy=None, save_dir='outputs', lang=language, resume=False, filter_replies=True, proximity=False,  limit=limit,
                    show_images=False,  geocode=None, minreplies=None, minlikes=None, minretweets=None)

    mlt = Multi_Tweets_Extraction()
    sentiments = Sentimment_Intensity_Analyzer()
    mlt_df = mlt.multi_tweets(tweets)
    df = pd.DataFrame(mlt_df)
    pre_clean_df = sentiments.pre_senti(df)

    if pre_clean_df.shape[0] > 0:
        wordcloud_vds_pos, wordcloud_vds_neg, vds_pos, vds_neg, df_vds = sentiments.vds_sentimental(
            pre_clean_df)
        print(f'Sample of Negative Tweets',
              df_vds.text_clean[df_vds['sentiments_vds'] == 'neg'])
        print(f'Sample of Postive Tweets ',
              df_vds.text_clean[df_vds['sentiments_vds'] == 'pos'])

    ## Visulazations ###
        print(df_vds)
        df_vds.to_csv('twitterData.csv')
        dict = df.to_dict('dict')
        word_cloud_viz(wordcloud_vds_pos)
        word_cloud_viz(wordcloud_vds_neg,
                       'WORDCLOUD FOR NEGATIVE TWEETS', "static/wc_neg.png")
        frequent_words_count(vds_pos)
        frequent_words_count(
            vds_neg, 'Top words used in Negative Tweets', "static/freq_neg.png")
        return render_template('results.html', data=dict)
    else:
        return "no data found"


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
