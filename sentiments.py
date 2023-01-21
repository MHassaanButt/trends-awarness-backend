from nltk.sentiment.vader import SentimentIntensityAnalyzer
# from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
import re
import string
import emoji
from multi_tweets_extraction import *
from scrape import *
from visulization import stop_words
# from flair.models import TextClassifier
# from flair.data import Sentence


class Sentimment_Intensity_Analyzer():
    def __init__(self, ):
        pass
    # In the following, the tweets' text will be cleaned by custom defined functions
    # Clean emojis from text
    def strip_emoji(self, text, **kwargs):
        print("In stirp emogi",type(text))
        return re.sub(emoji.get_emoji_regexp(), r"", text)  # remove emoji

    # Remove punctuations, links, mentions and \r\n new line characters
    def strip_all_entities(self, text, **kwargs):
        text = text.replace('\r', '').replace('\n', ' ').replace(
            '\n', ' ').lower()  # remove \n and \r and lowercase
        # remove links and mentions
        text = re.sub(r"(?:\@|https?\://)\S+", "", text)
        # remove non utf8/ascii characters such as '\x9a\x91\x97\x9a\x97'
        text = re.sub(r'[^\x00-\x7f]', r'', text)
        banned_list = string.punctuation + 'Ã'+'±'+'ã'+'¼'+'â'+'»'+'§'
        table = str.maketrans('', '', banned_list)
        text = text.translate(table)
        return text

    # clean hashtags at the end of the sentence, and keep those in the middle of the sentence by removing just the # symbol
    def clean_hashtags(self, tweet, **kwargs):
        new_tweet = " ".join(word.strip() for word in re.split(
            '#(?!(?:hashtag)\b)[\w-]+(?=(?:\s+#[\w-]+)*\s*$)', tweet))  # remove last hashtags
        # remove hashtags symbol from words in the middle of the sentence
        new_tweet2 = " ".join(word.strip()
                              for word in re.split('#|_', new_tweet))
        return new_tweet2

    # Filter special characters such as & and $ present in some words
    def filter_chars(self, a, **kwargs):
        sent = []
        for word in a.split(' '):
            if ('$' in word) | ('&' in word):
                sent.append('')
            else:
                sent.append(word)
        return ' '.join(sent)

    def remove_mult_spaces(self, text, **kwargs):  # remove multiple spaces
        return re.sub("\s\s+", " ", text)

    def remove_spam(self, text):
        match = re.search(r'subscribe', text)
        if match:
            return ''
        else:
            return text

    def pre_senti(self, df, **kwargs):
        # We apply all the three custom functions to the raw text of the tweets
        texts_new = []
        for t in df.orginal_tweet:
            texts_new.append(self.remove_spam(self.remove_mult_spaces(self.filter_chars(
                self.clean_hashtags(self.strip_all_entities(self.strip_emoji(t)))))))
        df['text_clean'] = texts_new
        # Moreover, we also make all the tweets to lower case.
        if df.shape[0] > 0:
            df['text_clean'] = df['text_clean'].str.lower()
        else:
            pass
        return df
    def polarity_to_text(self, vds_txt, **kwargs):
        if (vds_txt.get('compound') >= 0.05):
            return 'pos'
        elif(vds_txt.get('compound') > -0.05 and vds_txt.get('compound') < 0.05):
            return 'neu'
        else:
            return 'neg'
    


    def vds_sentimental(self, df, **kwargs):
        vds = SentimentIntensityAnalyzer()
        sentiments_vds = []
        for tweet in df.text_clean:
            vds_txt = vds.polarity_scores(tweet)
            sentiments_vds.append(self.polarity_to_text(vds_txt))
        df['sentiments_vds'] = sentiments_vds
        print("Distribution of Tweets Sentiments using VADER: \n",
              df['sentiments_vds'].value_counts(), "\n")
        stopwords = stop_words()
        vds_pos = " ".join(
            sentiment for sentiment in df[df['sentiments_vds'] == 'pos']['text_clean'])
        vds_neg = " ".join(
            sentiment for sentiment in df[df['sentiments_vds'] == 'neg']['text_clean'])
        if len(vds_pos) > 0:
            wordcloud_vds_pos = WordCloud(width=800,
                                          stopwords=stopwords,
                                          height=400,
                                          max_font_size=200,
                                          max_words=50,
                                          collocations=False,
                                          background_color='black').generate(vds_pos)
        else:
            wordcloud_vds_pos = WordCloud(width=800,
                                          stopwords=stopwords,
                                          height=400,
                                          max_font_size=200,
                                          max_words=50,
                                          collocations=False,
                                          background_color='black').generate('no_tweet_found')
        if len(vds_neg) > 0:
            wordcloud_vds_neg = WordCloud(width=800,
                                          stopwords=stopwords,
                                          height=400,
                                          max_font_size=200,
                                          max_words=50,
                                          collocations=False,
                                          background_color='black').generate(vds_neg)
        else:
            wordcloud_vds_neg = WordCloud(width=800,
                      stopwords=stopwords,
                      height=400,
                      max_font_size=200,
                      max_words=50,
                      collocations=False,
                      background_color='black').generate('no_tweet_found')
        return wordcloud_vds_pos, wordcloud_vds_neg, vds_pos, vds_neg, df