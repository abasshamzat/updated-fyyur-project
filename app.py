
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from models import Artist, db, Venue, Show

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)



def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime



@app.route('/')
def index():
  return render_template('pages/home.html')


@app.route('/venues')
def venues():
    data = []
    venues = Venue.query.all()

    places = Venue.query.distinct(Venue.city, Venue.state).all()

    for place in places:
        data.append({
        'city': place.city,
        'state': place.state,
        'venues': [{
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
        } for venue in venues if
            venue.city == place.city and venue.state == place.state]
    })
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    searchVenues = request.form.get("search_term", "")
    response = {"count": 0, "data": []}

    venue_search_results = (
        db.session.query(Venue)
        .filter(Venue.name.ilike(f"%{searchVenues}%"))
        .all()
    )
    response["count"] = len(venue_search_results)
    for result in venue_search_results:
        item = {
            "id": result.id,
            "name": result.name,
        }
        response["data"].append(item)
        return render_template(
            "pages/search_venues.html",
            results=response,
            search_term=request.form.get("search_term", "")
        )
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    upComingShows = []
    pastShows = []
    upcomingShowsNums = set([])
    pastShowsNums = set([])

    for show in (
        db.session.query(Show)
        .join(Artist)
        .filter(Show.venue_id == venue_id)
        .filter(Show.start_time > datetime.now())
        .all()
    ):
        upComingShows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        upcomingShowsNums.add(show.artist_id)

    for show in (
        db.session.query(Show)
        .join(Artist)
        .filter(Show.venue_id == venue_id)
        .filter(Show.start_time < datetime.now())
        .all()
    ):
        pastShows.append(
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        pastShowsNums.add(show.artist_id)

    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "genres": (venue.genres).split(","),
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "upcoming_shows_count": len(upcomingShowsNums),
        "upcoming_shows": upComingShows,
        "past_shows_count": len(pastShowsNums),
        "past_shows": pastShows,
    }

    return render_template("pages/show_venue.html", venue=data)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate_on_submit():
     error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        genres = request.form.getlist('genres')
        venue.genres = ','.join(genres)
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = request.form['seeking_talent']
        venue.seeking_description = request.form['seeking_description']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
                  request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
    return render_template('pages/home.html')
    
# Delete Venue

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

    venue_id = request.form.get('venue_id')
    deleted_venue = Venue.query.get(venue_id)
    venueName = deleted_venue.name
    try:
        db.session.delete(deleted_venue)
        db.session.commit()
        flash('Venue ' + venueName + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('please try again. Venue ' + venueName + ' could not be deleted.')
    finally:
        db.session.close()
        return redirect(url_for('index'))

@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name)
    data = []

    for artist in artists:
        data.append({
            "id": artist[0],
            "name": artist[1]
        })
    return render_template('pages/artists.html', artists=data) 

@app.route('/artists/search', methods=['POST'])
def search_artists():
    searchArtist = request.form.get("search_term", "")
    response = {"count": 0, "data": []}

    venue_search_results = (
        db.session.query(Artist)
        .filter(Artist.name.ilike(f"%{searchArtist}%"))
        .all()
    )
    response["count"] = len(venue_search_results)
    for result in venue_search_results:
        item = {
            "id": result.id,
            "name": result.name,
        }
        response["data"].append(item)
        return render_template(
            "pages/search_artists.html",
            results=response,
            search_term=request.form.get("search_term", "")
        )
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    upcomingShows = []
    pastShows = []

    for show in (
        db.session.query(Show)
        .join(Venue)
        .filter(Show.artist_id == artist_id)
        .filter(Show.start_time > datetime.now())
        .all()
    ):
        upcomingShows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    for show in (
        db.session.query(Show)
        .join(Venue)
        .filter(Show.artist_id == artist_id)
        .filter(Show.start_time < datetime.now())
        .all()
    ):
        pastShows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "genres": (artist.genres).split(","),
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "upcoming_shows_count": len(upcomingShows),
        "upcoming_shows": upcomingShows,
        "past_shows_count": len(pastShows),
        "past_shows": pastShows,
    }

    return render_template("pages/show_artist.html", artist=data)
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website.data = artist.website
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template("forms/edit_artist.html", form=form, artist=artist)
    

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
  
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template("forms/edit_venue.html", form=form, venue=venue)
    
  

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    error = False
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    if form.validate_on_submit():
     error = False
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        genres = request.form.getlist('genres')
        artist.genres = ','.join(genres)
        artist.website_link = request.form['website_link']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')

 # Shows       

@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": f'{show.start_time}',
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)
 

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    error = False
    try:
        show = Show()
        show.artist_id = request.form['artist_id']
        show.venue_id = request.form['venue_id']
        show.start_time = request.form['start_time']
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Requested show could not be listed.')
    else:
        flash('Requested show was successfully listed')
    return render_template('pages/home.html')
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

if __name__ == '__main__':
    app.run()

'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
