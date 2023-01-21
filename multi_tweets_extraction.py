import spacy
from scrape import *
import nltk
# nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
stop_words = set(stopwords.words('english'))
snlp = spacy.load("en_core_web_sm")


class Multi_Tweets_Extraction():
    def __init__(self,):
        pass

    def dup_function(self, x):
        return list(dict.fromkeys(x))
# UserScreenName,UserName, Likes,Retweets,Image link

    def multi_tweets(self, retrived_data):
        twr = {"tweet_id": [],  "UserScreenName": [], "UserName": [], "names": [], "nouns": [],
               "verbs": [], "cardinal_digit": [], "orginal_tweet": [], "Likes": [], "Retweets": [], "Image_link": []}
    #     tw_r={}
        for i in range(len(retrived_data)):
            text = retrived_data['Embedded_text'][i]
            UserScreenName = retrived_data['UserScreenName'][i]
            UserName = retrived_data['UserName'][i]
            Likes = retrived_data['Likes'][i]
            Retweets = retrived_data['Retweets'][i]
            Image_link = retrived_data['Image link'][i]
            tokenized = sent_tokenize(text)
            tag = []
            for j in tokenized:
                wordsList = nltk.word_tokenize(j)
                wordsList = [w for w in wordsList if not w in stop_words]
                tagged = nltk.pos_tag(wordsList)
                tag.append(tagged)
            nouns = []
            for k in tag:
                for l in range(len(k)):
                    if k[l][1] == 'NN' or k[l][1] == 'NNS':
                        nouns.append(k[l][0])
            nouns = self.dup_function(nouns)
            proper_noun = []
            for m in tag:
                for n in range(len(m)):
                    if m[n][1] == 'NNP' or m[n][1] == 'NNPS':
                        proper_noun.append(m[n][0])
            proper_noun = self.dup_function(proper_noun)
            complete_nouns = nouns+proper_noun
            complete_nouns = self.dup_function(complete_nouns)
            verbs = []
            for o in tag:
                for p in range(len(o)):
                    if o[p][1] == 'VB' or o[p][1] == 'VBD' or o[p][1] == 'VBG' or o[p][1] == 'VBN' or o[p][1] == 'VBP' or o[p][1] == 'VBZ':
                        verbs.append(o[p][0])
            verbs = self.dup_function(verbs)
            cardinal_digit = []
            for q in tag:
                for r in range(len(q)):
                    if q[r][1] == 'CD':
                        cardinal_digit.append(q[r][0])
            cardinal_digit = self.dup_function(cardinal_digit)
            texts = [text]
            docs = snlp.pipe(texts)
            names = []
            for doc in docs:
                names.extend(
                    [ent for ent in doc.ents if ent.label_ == "PERSON"])
            twr["tweet_id"].append(i)
            twr["UserScreenName"].append(UserScreenName)
            twr["UserName"].append(UserName)
            twr["names"].append(names)
            twr["nouns"].append(complete_nouns)
            twr["verbs"].append(verbs)
            twr["cardinal_digit"].append(cardinal_digit)
            twr["orginal_tweet"].append(text)
            twr["Likes"].append(Likes)
            twr["Retweets"].append(Retweets)
            twr["Image_link"].append(Image_link)
        return twr
