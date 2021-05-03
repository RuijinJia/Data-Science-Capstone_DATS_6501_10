# -*- coding: utf-8 -*-
"""Part3_Sentiment Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HIC1rFauD9Uj_b_8C6leNwlSSSuo2Y3r
"""

from google.colab import drive
import warnings
warnings.filterwarnings('ignore')
drive.mount('/content/drive')

abspath='/content/drive/MyDrive/capstone-netflix/'

import tensorflow as tf
import pandas as pd
import re
import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow_datasets as tfds
from nltk.tokenize.toktok import ToktokTokenizer
from nltk.tokenize import word_tokenize,sent_tokenize
from nltk.corpus import stopwords 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelBinarizer
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score,log_loss
from sklearn.feature_extraction.text import TfidfTransformer
import nltk
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
import pickle
from sklearn.svm import SVC 
from sklearn.feature_extraction.text import TfidfVectorizer
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from keras.layers import LSTM,Dense,Bidirectional,Input
from keras.models import Model
from tensorflow.keras.optimizers import Adam

review = pd.read_csv(abspath+"IMDB review.csv")

sns.set(style = "darkgrid" , font_scale = 1.2)
sns.countplot(review.sentiment)

review.sentiment = [ 1 if each == "positive" else 0 for each in review.sentiment]

le = LabelEncoder()

review['review'] = review['review'].apply(lambda x: re.sub('[,\.!?:()"]', '', x))
review['review'] = review['review'].apply(lambda x: re.sub('[^a-zA-Z"]', ' ', x))
review['review'] = review['review'].apply(lambda x: x.lower())

#removing the stopwords
stop_words = set(stopwords.words('english')) 
tokenizer=ToktokTokenizer()
def remove_stopwords(corpus):
    tokens = tokenizer.tokenize(corpus)
    tokens = [token.strip() for token in tokens]
    new_tokens = [token for token in tokens if token.lower() not in stop_words]
    new_text = ' '.join(new_tokens)    
    return new_text
#Apply function on review column
review['review']=review['review'].apply(remove_stopwords)

train_review,test_review,train_y,test_y  = train_test_split(review['review'].values,review['sentiment'].values,test_size = 0.2)
train_y_tran = le.fit_transform(train_y)
test_y_tran = le.fit_transform(test_y)

tokenizer = Tokenizer(num_words=15000,oov_token='<OOV>')
tokenizer.fit_on_texts(train_review)
word_index = tokenizer.word_index

train_sequence = tokenizer.texts_to_sequences(train_review)
test_sequence = tokenizer.texts_to_sequences(test_review)
train_pad_sequence = pad_sequences(train_sequence,maxlen = 200,truncating= 'post',padding = 'pre')
test_pad_sequence = pad_sequences(test_sequence,maxlen = 200,truncating= 'post',padding = 'pre')
print('Total Unique Words : {}'.format(len(word_index)))

embedded_words = {}
# with open('glove.6B.200d.txt') as file:
with open('/content/drive/MyDrive/capstone-netflix/glove.6B.200d.txt') as file:
    for line in file:
        words, coeff = line.split(maxsplit=1)
        coeff = np.array(coeff.split(),dtype = float)
        embedded_words[words] = coeff

embedding_matrix = np.zeros((len(word_index) + 1,200))
for word, i in word_index.items():
    embedding_vector = embedded_words.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector

LSTM_model = tf.keras.Sequential([tf.keras.layers.Embedding(len(word_index) + 1,200,weights=[embedding_matrix],input_length=200,
                            trainable=False),
                             tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64)),
                             tf.keras.layers.Dropout(0.3),
                             tf.keras.layers.Dense(256,activation = 'relu',),
                             tf.keras.layers.Dense(128,activation = 'relu'),
                             tf.keras.layers.Dropout(0.3),
                             tf.keras.layers.Dense(1,activation = tf.nn.sigmoid)])

LSTM_model.summary()

LSTM_model.compile(loss = tf.keras.losses.BinaryCrossentropy() , optimizer='Adam' , metrics = 'accuracy')
LSTM_history = LSTM_model.fit(train_pad_sequence,train_y_tran,epochs = 6 ,validation_data=(test_pad_sequence,test_y_tran))

LSTM_acc = LSTM_history.history['accuracy']
LSTM_val_acc = LSTM_history.history['val_accuracy']
LSTM_loss = LSTM_history.history['loss']
LSTM_val_loss = LSTM_history.history['val_loss']
LSTM_epochs = range(len(LSTM_acc))

plt.plot(LSTM_epochs, LSTM_acc, 'r', label='Training accuracy')
plt.plot(LSTM_epochs, LSTM_val_acc, 'b', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.xlabel('epochs')
plt.ylabel('Accuracy')
plt.legend(loc=0)
plt.figure()

plt.plot(LSTM_epochs, LSTM_loss, 'r', label='Training loss')
plt.plot(LSTM_epochs, LSTM_val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('epochs')
plt.ylabel('Loss')
plt.legend(loc=0)
plt.show()

print('Training Accuracy: {}'.format(max(LSTM_acc)))
print('Validation Accuracy: {}'.format(max(LSTM_val_acc)))

LSTM_pred = LSTM_model.predict(test_pad_sequence)
LSTM_pred = np.round(LSTM_pred).astype(int)

LSTM_cm = confusion_matrix(le.fit_transform(test_y),le.fit_transform(LSTM_pred))

plt.figure(figsize = (10,10))
sns.heatmap(LSTM_cm,cmap= "Blues", linecolor = 'black' , linewidth = 1 , annot = True, fmt='' , xticklabels = ['Negative','Positive'] , yticklabels = ['Negative','Positive'])
plt.xlabel("Predicted Reviews")
plt.ylabel("Actual Reviews")

"""SVM"""

def feature_extraction(data):
    tfv=TfidfVectorizer(sublinear_tf=True, stop_words = "english")
    features=tfv.fit_transform(data)
    pickle.dump(tfv.vocabulary_, open("svm_feature.pkl", "wb"))
    return features

def preprocess(sample):
    sample.lower()
    sample = re.sub('[,\.!?:()"]','',sample)
    sample = re.sub('[^a-zA-Z"]','', sample)
    sample = re.sub('[\s]+', ' ', sample)
    tokens = word_tokenize(sample)
    tokens = [w for w in tokens if not w in stop_words]
    return " ".join(tokens)

data = np.array(review.review)
label = np.array(review.sentiment)
features = feature_extraction(data)

X_train, X_test, Y_train, Y_test = train_test_split(features, label, test_size = 0.20)

svclassifier = SVC(kernel='linear')  
svclassifier.fit(X_train, Y_train)

svm_pred = svclassifier.predict(X_test)
print('Validation Accuract is: ', accuracy_score(Y_test, svm_pred))
print('Validation Loss is:', log_loss(Y_test, svm_pred))

#save svm model
filename = 'svm_model.sav'
pickle.dump(svclassifier, open(filename, 'wb'))

loaded_model = pickle.load(open(filename, 'rb'))

# sample1 = "3 Idiots is an evergreen Bollywood movie. The Aamir Khan starrer movie is a great mixture of several genre like comedy ,drama and romance.  I highly recommend this movie. The movie talks about several life experiences in humorous tones. Other great actors like Sharman Joshi aka 'Raju' , Madhavan aka 'Farhan' , Omi Vaidya as 'Silencer' , KKK as 'Piya' and Boman Irani as 'Virus' made this movie a huge success."
sample1 = 'My friend showed me this movie a few months ago, And we watched the 2nd movie, I thought that Noah and Elles relationship was cute and romantic. Until I watched the first one and re-watched the second one, I dont get why Elle chose Noah at the end of the first movie and the second one, He controls Elle so much, I agree with Lees perspective about their relationship, Why would Noah not let any other guy be with Elle, When he hooks up with every girl in their high school. Now onto Elle, In the second movie she has a dance competition with new kid Marco, And when they finish they kiss, And Noah leaves the building because obviously he would be mad, And Elle tries having him forgive her, WHY WOULD HE YOU KISSED ANOTHER BOY AND YOU ARE IN A RELATIONSHIP. If I could get rid of The Kissing Booth 1 off Netflix, I would, Watch a better movie like Enola Holmes.'
sample1 = preprocess(sample1)
sample1 = np.array([sample1])

transformer = TfidfTransformer()
tfv_loaded = TfidfVectorizer(sublinear_tf=True, stop_words = "english", vocabulary=pickle.load(open("svm_feature.pkl", "rb")))
text = transformer.fit_transform(tfv_loaded.fit_transform(sample1))
polarity = loaded_model.predict(text)
print(polarity)

SVM_history = svclassifier.fit(X_train,Y_train)

SVM_acc = SVM_history.history['accuracy']
SVM_val_acc = SVM_history.history['val_accuracy']
SVM_loss = SVM_history.history['loss']
SVM_val_loss = SVM_history.history['val_loss']
SVM_epochs = range(len(SVM_acc))

plt.plot(SVM_epochs, SVM_acc, 'r', label='Training accuracy')
plt.plot(SVM_epochs, SVM_val_acc, 'b', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.xlabel('epochs')
plt.ylabel('Accuracy')
plt.legend(loc=0)
plt.figure()

svm_cm = confusion_matrix(le.fit_transform(Y_test),le.fit_transform(svm_pred))

plt.figure(figsize = (10,10))
sns.heatmap(svm_cm,cmap= "Blues", linecolor = 'black' , linewidth = 1 , annot = True, fmt='' , xticklabels = ['Bad Reviews','Good Reviews'] , yticklabels = ['Bad Reviews','Good Reviews'])
plt.xlabel("Predicted")
plt.ylabel("Actual")

"""BERT"""

!pip install transformers sentencepiece
!pip install tokenizers
from tokenizers import BertWordPieceTokenizer
import transformers
tokenizer = transformers.DistilBertTokenizer.from_pretrained('distilbert-base-uncased' , lower = True)
# Save the loaded tokenizer locally
tokenizer.save_pretrained('.')
# Reload it with the huggingface tokenizers library
bert_tokenizer = BertWordPieceTokenizer('vocab.txt', lowercase=True)
bert_tokenizer

def fast_encode(texts, tokenizer):

    tokenizer.enable_truncation(max_length=400)
    tokenizer.enable_padding()
    all_ids = []
    
    for i in range(0, len(texts), 256):
        text_chunk = texts[i:i+256].tolist()
        encs = tokenizer.encode_batch(text_chunk)
        all_ids.extend([enc.ids for enc in encs])
    
    return np.array(all_ids)

review = pd.read_csv(abspath+"IMDB review.csv")
review.sentiment = [ 1 if each == "positive" else 0 for each in review.sentiment]
train_review,test_review,train_y,test_y  = train_test_split(review['review'],review['sentiment'],test_size = 0.2)

x_train = fast_encode(train_review.values, bert_tokenizer)
x_test = fast_encode(test_review.values, bert_tokenizer)

def buildmodel(transformer):
    
    id = Input(shape=(400,), dtype=tf.int32, name="id")
    output = transformer(id)[0]
    token = output[:, 0, :]
    out = Dense(1, activation='sigmoid')(token)
    
    model = Model(inputs=id, outputs=out)
    model.compile(Adam(lr=2e-5), loss='binary_crossentropy', metrics=['accuracy'])
    
    return model

bert1 = transformers.TFDistilBertModel.from_pretrained('distilbert-base-uncased')

bert = buildmodel(bert1)
bert.summary()

history = bert.fit(x_train,train_y,batch_size = 32 ,validation_data=(x_test,test_y),epochs = 3)

print("Accuracy of the model on Testing Data is " , bert.evaluate(x_test,test_y)[1]*100 , "%")

bert_epochs = [i for i in range(3)]
bert_train_acc = history.history['accuracy']
bert_train_loss = history.history['loss']
bert_val_acc = history.history['val_accuracy']
bert_val_loss = history.history['val_loss']

bert_acc = history.history['accuracy']
bert_val_acc = history.history['val_accuracy']
bert_loss = history.history['loss']
bert_val_loss = history.history['val_loss']
bert_epochs = range(len(bert_acc))

plt.plot(bert_epochs, bert_acc, 'r', label='Training accuracy')
plt.plot(bert_epochs, bert_val_acc, 'b', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.legend(loc=0)
plt.figure()

plt.plot(bert_epochs, bert_loss, 'r', label='Training loss')
plt.plot(bert_epochs, bert_val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.legend(loc=0)

plt.show()

bert_pred_ori = bert.predict(x_test)
bert_pred = np.round(bert_pred_ori).astype(int)
bert_cm = confusion_matrix(test_y,bert_pred)

plt.figure(figsize = (10,10))
sns.heatmap(bert_cm,cmap= "Blues", linecolor = 'black' , linewidth = 1 , annot = True, fmt='' , xticklabels = ['Negative','Positive'] , yticklabels = ['Negative','Positive'])
plt.xlabel("Predicted Reviews")
plt.ylabel("Actual Reviews")

test_review.values

text_sample = np.array(['My one of the favourite lines from the movie was...joker saying to himself,,,"I used to think that my life is a TRAGEDY but now i realise that it is nothing but COMEDY"....so, u can imagine how disturbing a movie could be with its theme being TRAGEDY=COMEDY...but it was not that disturbing for me as i am used to of or aware of the ongoing social-political structure of our country','"It has dwarfs, music, Technicolor, freak characters, and Judy Garland. It cant be expected to have a sense of humor as well, and as for the light touch of fantasy, it weighs like a pound of fruitcake soaking wet.'])
text_sample_encoder = fast_encode(text_sample, bert_tokenizer)

test_review_ind = np.array(test_review)

test_review_ind[3]

bert_pred_ori[3]