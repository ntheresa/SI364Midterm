###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, ValidationError, TextAreaField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
import json, requests

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'this is a hard to guess string'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://localhost/364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

YELP_URL = 'https://api.yelp.com/v3/businesses/search'
YELP_KEY = 'WBvJCMpJ0u6MIVgf6NCdH-uBWP_1NGafugipiNj5llmccREeFa5bxdVDlJDC9_FibDR2s_VkyvTKDaG2Z2aLv0bjvwyNDtkOUtimCoZbE-Rbo8YMC9dQYrx6657PWnYx'
HEADERS = {'Authorization': 'Bearer ' + YELP_KEY,}


## Statements for db setup (and manager setup if using Manager)
manager = Manager(app)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Search(db.Model):
    __tablename__ = 'search'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(64))
    food_type = db.Column(db.String(64))


class Restaurants(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(240))
    food_type = db.Column(db.String(64))
    location = db.Column(db.String(164))
    restaurant_reviews = db.relationship('Reviews', backref='Restaurants')

class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    rating = db.Column(db.String(10))
    review = db.Column(db.String(1000))

###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name to get started! ",validators=[Required()])
    submit = SubmitField()

class SearchForm(FlaskForm):
    city = StringField("Enter the city you want to find restaurants in: ", validators=[Required()])
    food_type = StringField("What kind of food are you looking for? (Italian, Mexican, American, Chinese, etc.) ", validators=[Required()])
    def validate_food_type(form, field):
        if len(field.data.split()) > 1:
            raise ValidationError('You can only choose one type of food to search for.')
    submit = SubmitField()

class RestaurantForm(FlaskForm):
    restaurant_name = StringField("Enter the name of your favorite restaurant: ", validators=[Required()])
    rating = StringField("What rating would you give it? (1 - 5)", validators=[Required()])
    food_type = StringField("What kind of food is it? (Italian, Mexican, American, Chinese, etc.)",validators=[Required()])
    def validate_food_type(form, field):
        if len(field.data.split()) > 1:
            raise ValidationError('You can only choose one type of food to search for.')
    location = StringField("Where is the restaurant located? ", validators=[Required()])
    review = TextAreaField("Enter your review of the restaurant: ", validators=[Required()])
    submit = SubmitField()
#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/', methods =['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('namepage.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/find_restaurant', methods =['GET', 'POST'])
def find_restaurant():
    form = SearchForm()
    if form.validate_on_submit():
        city = form.city.data
        food_type = form.food_type.data
        restaurant = Search.query.filter_by(city=city, food_type=food_type).first()
        if not restaurant:
            restaurant = Search(city=city, food_type=food_type)
            db.session.add(restaurant)
            db.session.commit()
        params = {}
        params['location'] = city
        params['limit'] = 10
        params['categories'] = food_type
        req = requests.get(YELP_URL ,params=params, headers=HEADERS)
        all_restaurants = []
        results = json.loads(req.text)
        for r in results['businesses']:
            restaurant = {}
            restaurant['name'] = r['name']
            restaurant['rating'] = r['rating']
            restaurant['price'] = r['price']
            restaurant['url'] = r['url']
            all_restaurants.append(restaurant)
        return render_template('find_restaurant.html', form=form, all_restaurants=all_restaurants)
    return render_template('find_restaurant.html',form=form)


@app.route('/restaurants_review', methods =['GET', 'POST'])
def restaurants_review():
    form = RestaurantForm()
    if form.validate_on_submit():
        restaurant_name = form.restaurant_name.data
        rating = form.rating.data
        food_type = form.food_type.data
        location = form.location.data
        review = form.review.data

        restaurant = Restaurants.query.filter_by(name=restaurant_name).first()
        if not restaurant:
            restaurant = Restaurants(name=restaurant_name,food_type=food_type, location=location)
            db.session.add(restaurant)
            db.session.commit()


        review = Reviews(restaurant_id=restaurant.id, rating=rating,review=review)
        db.session.add(review)
        db.session.commit()
        flash('Review has been successfully added!')
        return redirect(url_for('restaurants_review'))
    return render_template('restaurants_review_form.html', form=form)

@app.route('/reviews')
def reviews():
    all_reviews = Reviews.query.all()
    all_restaurants = Restaurants.query.all()
    return render_template('restaurant_reviews.html',all_reviews=all_reviews)
## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
