import os
from flask import Flask, request, redirect, url_for,flash
from werkzeug.utils import secure_filename
import flask
from flask import render_template
import numpy as np
import io
import pickle
from PIL import Image
from flask import jsonify
#from pickle import load,dump
#from numpy import array
from keras.layers import LSTM, Embedding, Dense,Dropout
#import pandas as pd
from keras.applications.inception_v3 import InceptionV3
#from keras.preprocessing import image
from keras.models import Model
from keras.layers.merge import add
from keras.applications.inception_v3 import preprocess_input
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing import image
from keras import Input

global model,model_new
vocab_size=1652
max_length=32
embedding_dim = 200
inputs1 = Input(shape=(2048,))
fe1 = Dropout(0.5)(inputs1)
fe2 = Dense(256, activation='relu')(fe1)
inputs2 = Input(shape=(max_length,))
se1 = Embedding(vocab_size, embedding_dim, mask_zero=True)(inputs2)
se2 = Dropout(0.5)(se1)
se3 = LSTM(256)(se2)
decoder1 = add([fe2, se3])
decoder2 = Dense(256, activation='relu')(decoder1)
outputs = Dense(vocab_size, activation='softmax')(decoder2)
model = Model(inputs=[inputs1, inputs2], outputs=outputs)
global resp
app=Flask(__name__)
@app.route("/")
def hello():
	return render_template('index.html')

def load_model():
    global model,model_new,ixtoword,wordtoix
    modelin=InceptionV3(weights='imagenet')
    model_new=Model(modelin.input,modelin.layers[-2].output)
    model.load_weights('model_30.h5')
    with open('indextoword.pkl','rb') as f:
        ixtoword=pickle.load(f)
    with open('wordtoindex.pkl','rb') as f:
        wordtoix=pickle.load(f)
def preprocess(photo,target_size):
    # Convert all the images to size 299x299 as expected by the inception v3 model
    img = photo.resize(target_size)
    # Convert PIL image to numpy array of 3-dimensions
    x = image.img_to_array(img)
    # Add one more dimension
    x = np.expand_dims(x, axis=0)
    # preprocess the images using preprocess_input() from inception module
    x = preprocess_input(x)
    return x

@app.route("/predict", methods=['POST','GET'])
def upload():
    data = {"success": False}
    if flask.request.method == "POST":
        if flask.request.files.get("file"):
            # read the image in PIL format
            photo = flask.request.files["file"].read()
            photo = Image.open(io.BytesIO(photo))
    photo = preprocess(photo,target_size=(299,299)) # preprocess the image
    fea_vec = model_new.predict(photo) # Get the encoding vector for the image
    fea_vec = np.reshape(fea_vec, fea_vec.shape[1]) # reshape from (1, 2048) to (2048, )
    photo =fea_vec.reshape((1,2048))
    in_text = 'startseq'
    for i in range(max_length):
        sequence = [wordtoix[w] for w in in_text.split() if w in wordtoix]
        sequence = pad_sequences([sequence], maxlen=max_length)
        yhat = model.predict([photo,sequence], verbose=0)
        yhat = np.argmax(yhat)
        word = ixtoword[yhat]
        in_text += ' ' + word
        if word == 'endseq':
            break
    final = in_text.split()
    final = final[1:-1]
    final = ' '.join(final)
#    data["final"]=[]
 #   data["final"]=final
  #  data["success"] = True
    return jsonify({"final":final})

if __name__ == "__main__":
    print(("* Loading Keras model and Flask starting server..."
        "please wait until server has fully started"))
    load_model()
    app.run(host='0.0.0.0',port=5000,threaded=False)