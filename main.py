from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import db

app = Flask(__name__)
app.secret_key = 'pinkbird_secret_key'  # needed for flash messages

# init flask app
# rtsb - run the server baby
@app.route('/')
def index():
    tweets = db.get_all_tweets()
    return render_template('index.html', tweets=tweets)

# create new tweet
# ptp - post the post
@app.route('/tweet', methods=['POST'])
def post_tweet():
    user = request.form['user']
    content = request.form['content']
    thread_id = request.form.get('thread_id')
    
    # convert thread_id to int or None
    if thread_id:
        thread_id = int(thread_id)
    
    # call the db function which uses the stored procedure
    post_id = db.publish_tweet(user, content, thread_id)
    
    return redirect(url_for('index'))

# follow a user 
# fau - follow a user
@app.route('/follow', methods=['POST'])
def follow():
    follower_id = request.form['follower_id']
    following_id = request.form['following_id']
    
    success = db.follow_user(follower_id, following_id)
    
    if success:
        flash('Successfully followed user')
    else:
        flash('Already following this user')
    
    return redirect(request.referrer or url_for('index'))

# unfollow a user
# uau - unfollow a user
@app.route('/unfollow', methods=['POST'])
def unfollow():
    follower_id = request.form['follower_id']
    following_id = request.form['following_id']
    
    success = db.unfollow_user(follower_id, following_id)
    
    if success:
        flash('Successfully unfollowed user')
    else:
        flash('Not following this user')
    
    return redirect(request.referrer or url_for('index'))

# like a post
# lap - like a post
@app.route('/like', methods=['POST'])
def like():
    user_id = request.form['user_id']
    post_id = int(request.form['post_id'])
    
    success = db.like_post(user_id, post_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    return redirect(request.referrer or url_for('index'))

# unlike a post
# ulp - unlike a post
@app.route('/unlike', methods=['POST'])
def unlike():
    user_id = request.form['user_id']
    post_id = int(request.form['post_id'])
    
    success = db.unlike_post(user_id, post_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success})
    
    return redirect(request.referrer or url_for('index'))

# start app
# rsdm - run server in debug mode
if __name__ == '__main__':
    app.run(debug=True)
