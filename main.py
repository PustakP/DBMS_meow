from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
import db as db
import functools
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'pinkbird_secret_key'  # needed for flash messages
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Make db module available to all templates
@app.context_processor
def inject_db():
    return dict(db=db)

# Authentication decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get('user_id') is None:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

# Set current user for each request
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.get_user(user_id)

# index/home route - show feed if logged in, or splash screen if not
@app.route('/')
def index():
    if g.user:
        tweets = db.get_feed_tweets(g.user['user_id'])
        return render_template('index.html', tweets=tweets)
    else:
        return render_template('welcome.html')

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        bio = request.form.get('bio', '')
        
        # Handle profile picture upload
        profile_pic = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                profile_pic = 'uploads/' + filename
        
        success, message = db.create_user(username, email, password, bio, profile_pic)
        
        if success:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        
        user = db.authenticate_user(username_or_email, password)
        
        if user:
            session.clear()
            session['user_id'] = user['user_id']
            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# Profile page
@app.route('/profile/<username>')
def profile(username):
    user = db.get_user_by_username(username)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    
    tweets = db.get_user_tweets(user['user_id'])
    follower_count = db.get_follower_count(user['user_id'])
    following_count = db.get_following_count(user['user_id'])
    
    # Check if the logged-in user is following this profile
    is_following = False
    if g.user:
        is_following = db.is_following(g.user['user_id'], user['user_id'])
    
    return render_template('profile.html', 
                          profile_user=user, 
                          tweets=tweets, 
                          follower_count=follower_count, 
                          following_count=following_count,
                          is_following=is_following)

# Edit profile
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        
        # Handle profile picture upload
        profile_pic = g.user['profile_pic']
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                profile_pic = 'uploads/' + filename
        
        success = db.update_profile(g.user['user_id'], bio, profile_pic)
        
        if success:
            flash('Profile updated successfully', 'success')
        else:
            flash('Failed to update profile', 'error')
        
        return redirect(url_for('profile', username=g.user['username']))
    
    return render_template('edit_profile.html', user=g.user)

# Show followers
@app.route('/profile/<username>/followers')
def followers(username):
    user = db.get_user_by_username(username)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    
    followers = db.get_followers(user['user_id'])
    
    return render_template('followers.html', profile_user=user, followers=followers)

# Show following
@app.route('/profile/<username>/following')
def following(username):
    user = db.get_user_by_username(username)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    
    following = db.get_following(user['user_id'])
    
    return render_template('following.html', profile_user=user, following=following)

# create new tweet
@app.route('/tweet', methods=['POST'])
@login_required
def post_tweet():
    content = request.form['content']
    thread_id = request.form.get('thread_id')
    
    # convert thread_id to int or None
    if thread_id:
        thread_id = int(thread_id)
    
    # call the db function which uses the stored procedure
    post_id = db.publish_tweet(g.user['user_id'], content, thread_id)
    
    if thread_id:
        return redirect(url_for('view_tweet', tweet_id=thread_id))
    
    return redirect(url_for('index'))

# View a single tweet and its replies
@app.route('/tweet/<int:tweet_id>')
def view_tweet(tweet_id):
    tweet = db.get_tweet(tweet_id)
    
    if not tweet:
        flash('Tweet not found', 'error')
        return redirect(url_for('index'))
    
    replies = db.get_tweet_replies(tweet_id)
    
    # Check if the user has liked this tweet
    is_liked = False
    if g.user:
        is_liked = db.is_post_liked(g.user['user_id'], tweet_id)
    
    return render_template('tweet.html', tweet=tweet, replies=replies, is_liked=is_liked)

# Search route
@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    if query.startswith('#'):
        # Search for hashtag
        hashtag = query[1:]
        tweets = db.search_tweets_by_hashtag(hashtag)
        return render_template('search_results.html', query=query, tweets=tweets, hashtag=hashtag)
    else:
        # Search for users
        users = db.search_users(query)
        return render_template('search_results.html', query=query, users=users)

# follow a user 
@app.route('/follow', methods=['POST'])
@login_required
def follow():
    following_id = request.form['following_id']
    
    success = db.follow_user(g.user['user_id'], following_id)
    
    if success:
        flash('Successfully followed user')
    else:
        flash('Already following this user')
    
    return redirect(request.referrer or url_for('index'))

# unfollow a user
@app.route('/unfollow', methods=['POST'])
@login_required
def unfollow():
    following_id = request.form['following_id']
    
    success = db.unfollow_user(g.user['user_id'], following_id)
    
    if success:
        flash('Successfully unfollowed user')
    else:
        flash('Not following this user')
    
    return redirect(request.referrer or url_for('index'))

# like a post
@app.route('/like', methods=['POST'])
@login_required
def like():
    post_id = int(request.form['post_id'])
    
    success = db.like_post(g.user['user_id'], post_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    return redirect(request.referrer or url_for('index'))

# unlike a post
@app.route('/unlike', methods=['POST'])
@login_required
def unlike():
    post_id = int(request.form['post_id'])
    
    success = db.unlike_post(g.user['user_id'], post_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    return redirect(request.referrer or url_for('index'))

# Explore page - show all tweets
@app.route('/explore')
def explore():
    tweets = db.get_all_tweets()
    return render_template('explore.html', tweets=tweets)

# start app
if __name__ == '__main__':
    app.run(debug=True)
