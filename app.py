import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import urllib.request
import pickle
import requests



similarity=pickle.load(open("C:/Users/Yogesh Computers/AppData/Local/Programs/Python/Python310/Movie Recommender System and Sentiment Analysis/similarity.pkl",'rb'))
vectorizer=pickle.load(open("C:/Users/Yogesh Computers/AppData/Local/Programs/Python/Python310/Movie Recommender System and Sentiment Analysis/npl_vectorizer.pkl",'rb'))
model=pickle.load(open("C:/Users/Yogesh Computers/AppData/Local/Programs/Python/Python310/Movie Recommender System and Sentiment Analysis/reviews_model.pkl",'rb'))

movies_df=pd.read_csv('top50.csv')
movies=pd.read_csv('dataset.csv')


app = Flask(__name__)

@app.route('/')
def index():
    movie_data = []
    for _, row in movies_df.iterrows():
        movie_id = row['movie_id']
        title = row['title']
        poster_url = fetch_poster(movie_id)
        movie_data.append({'title': title, 'poster_url': poster_url})
    return render_template('index.html', movies=movie_data)


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')


@app.route('/recommend',methods=['post'])
def recommend():
    data=[]
    movie=request.form.get('movie')
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    # make sure there are at least 5 movies in distances
    if len(distances) < 5:
        distances = distances[:len(distances)]
    recommended_movie_details = []
    for i in distances:
        # skip the movie itself
        if i[0] == index:
            continue
        # fetch the movie details
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_details.append({
            'title': movies.iloc[i[0]].title,
            'poster_path': fetch_poster(movie_id),
            'imdb_id': imdb_id(movie_id)
        })
        # stop after collecting 5 movies
        if len(recommended_movie_details) >= 5:
            break
    return render_template('recommend.html', recommended_movie_details=recommended_movie_details)


@app.route('/reviews', methods=['POST'])
def reviews():
    imdb_id = request.form.get('imdb_id')
    movie_reviews = fetch_reviews(imdb_id)
    return render_template('reviews.html', movie_reviews=movie_reviews)


def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=db7e7d795b0b5d27a18a0610b109c301&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def imdb_id(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=db7e7d795b0b5d27a18a0610b109c301&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    imdb_id = data['imdb_id']
    return imdb_id

def fetch_reviews(imdb_id):
    sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).read()
    soup = BeautifulSoup(sauce,'html.parser')
    soup_result = soup.find_all("div",{"class":"text show-more__control"})
    
    reviews_list = [] # list of reviews
    reviews_status = [] # list of comments (good or bad)
    for reviews in soup_result:
        if reviews.string:
            reviews_list.append(reviews.string)
            # passing the review to our model
            movie_review_list = np.array([reviews.string])
            movie_vector = vectorizer.transform(movie_review_list)
            pred =model.predict(movie_vector)
            reviews_status.append('Good' if pred else 'Bad')

    # combining reviews and comments into a dictionary
    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))} 
    
    return movie_reviews



if __name__=='__main__':
    app.run(debug=True)