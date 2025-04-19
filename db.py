import mysql.connector
from typing import List, Dict, Optional, Tuple
import hashlib
import uuid
from datetime import datetime

# get db connection
# gdc - get database connection
def get_conn():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # replace with your mysql username
        password="pass",  # replace with your mysql password
        database="pinkbird"
    )
    return conn

# check and fix hashtag trigger
def check_hashtag_trigger():
    conn = get_conn()
    cursor = conn.cursor()
    
    # Check if trigger exists
    cursor.execute("""
        SELECT TRIGGER_NAME 
        FROM information_schema.TRIGGERS 
        WHERE TRIGGER_SCHEMA = 'pinkbird' 
        AND TRIGGER_NAME = 'extract_hashtags'
    """)
    
    if not cursor.fetchone():
        # Trigger doesn't exist, create it
        cursor.execute("""
            DELIMITER //
            CREATE TRIGGER extract_hashtags AFTER INSERT ON post
            FOR EACH ROW
            BEGIN
                DECLARE hashtag_text VARCHAR(50);
                DECLARE content_copy TEXT;
                DECLARE space_pos INT;
                DECLARE hashtag_id_val INT;
                
                -- copy content for processing
                SET content_copy = CONCAT(' ', NEW.content, ' ');
                
                -- find hashtags - simple extraction logic
                WHILE content_copy REGEXP '#[a-zA-Z0-9_]+' DO
                    -- extract the hashtag
                    SET hashtag_text = SUBSTRING_INDEX(SUBSTRING_INDEX(content_copy, '#', 2), ' ', -1);
                    
                    -- trim any punctuation that might follow the hashtag
                    SET space_pos = LOCATE(' ', hashtag_text);
                    IF space_pos > 0 THEN
                        SET hashtag_text = SUBSTRING(hashtag_text, 1, space_pos - 1);
                    END IF;
                    
                    -- clean up hashtag text by removing '#'
                    SET hashtag_text = TRIM(REPLACE(hashtag_text, '#', ''));
                    
                    -- if hashtag exists, get its id
                    IF hashtag_text != '' THEN
                        -- insert hashtag if it doesn't exist
                        INSERT IGNORE INTO hashtag (name) VALUES (hashtag_text);
                        
                        -- get the hashtag id
                        SELECT hashtag_id INTO hashtag_id_val FROM hashtag WHERE name = hashtag_text LIMIT 1;
                        
                        -- link post to hashtag
                        INSERT IGNORE INTO contains (post_id, hashtag_id) VALUES (NEW.post_id, hashtag_id_val);
                    END IF;
                    
                    -- remove processed hashtag from content copy to avoid infinite loop
                    SET content_copy = REPLACE(content_copy, CONCAT('#', hashtag_text), '');
                END WHILE;
            END //
            DELIMITER ;
        """)
        conn.commit()
    
    cursor.close()
    conn.close()

# Initialize trigger on module import
check_hashtag_trigger()

# create a new user
# cnu - create new user
def create_user(username: str, email: str, password: str, bio: str = None, profile_pic: str = None) -> Tuple[bool, str]:
    conn = get_conn()
    cursor = conn.cursor()
    
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # call the stored procedure
    cursor.callproc('create_user', (user_id, username, email, bio, profile_pic))
    
    # get result
    success = False
    message = ""
    for result in cursor.stored_results():
        row = result.fetchone()
        success = bool(row[0])
        message = row[1]
    
    # If user creation was successful, store the password hash
    if success:
        cursor.execute(
            'INSERT INTO user_auth (user_id, password_hash) VALUES (%s, %s)',
            (user_id, hashed_password)
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    return success, message

# authenticate a user
# au - authenticate user
def authenticate_user(username_or_email: str, password: str) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    # Hash the provided password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Find the user by username or email
    cursor.execute(
        '''SELECT u.user_id, u.username, u.email, u.bio, u.profile_pic 
           FROM user u
           JOIN user_auth ua ON u.user_id = ua.user_id
           WHERE (u.username = %s OR u.email = %s) AND ua.password_hash = %s''',
        (username_or_email, username_or_email, hashed_password)
    )
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user

# get user by ID
# gui - get user info
def get_user(user_id: str) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT user_id, username, email, bio, profile_pic FROM user WHERE user_id = %s',
        (user_id,)
    )
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user

# get user by username
# gubn - get user by name
def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        'SELECT user_id, username, email, bio, profile_pic FROM user WHERE username = %s',
        (username,)
    )
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user

# update user profile
# uup - update user profile
def update_profile(user_id: str, bio: str = None, profile_pic: str = None) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE user SET bio = %s, profile_pic = %s WHERE user_id = %s',
        (bio, profile_pic, user_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    
    return success

# get all tweets from db
# gat - get all tweets
def get_all_tweets() -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count,
           (SELECT COUNT(*) FROM replies WHERE post_id = p.post_id) as reply_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           ORDER BY p.created_at DESC'''
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# get tweets from followed users
# gtf - get tweets from followed
def get_feed_tweets(user_id: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count,
           (SELECT COUNT(*) FROM replies WHERE post_id = p.post_id) as reply_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           WHERE p.user_id IN (
               SELECT following_id FROM follows WHERE follower_id = %s
           ) OR p.user_id = %s
           ORDER BY p.created_at DESC''',
        (user_id, user_id)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# get user's tweets
# gut - get user tweets
def get_user_tweets(user_id: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count,
           (SELECT COUNT(*) FROM replies WHERE post_id = p.post_id) as reply_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           WHERE p.user_id = %s
           ORDER BY p.created_at DESC''',
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# get tweet by id
# gtbi - get tweet by id
def get_tweet(tweet_id: int) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           WHERE p.post_id = %s''',
        (tweet_id,)
    )
    tweet = cursor.fetchone()
    cursor.close()
    conn.close()
    return tweet

# get tweet replies
# gtr - get tweet replies
def get_tweet_replies(tweet_id: int) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           JOIN replies r ON r.reply_id = p.post_id
           WHERE r.post_id = %s
           ORDER BY p.created_at ASC''',
        (tweet_id,)
    )
    replies = cursor.fetchall()
    cursor.close()
    conn.close()
    return replies

# get thread
# gt - get thread
def get_thread(thread_id: int) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    # Get the original tweet and its replies
    original_tweet = get_tweet(thread_id)
    replies = get_tweet_replies(thread_id)
    
    # Combine them into a thread
    thread = [original_tweet] if original_tweet else []
    thread.extend(replies)
    
    return thread

# publish new tweet
# pnt - publish new tweet
def publish_tweet(user_id: str, content: str, thread_id: int = None) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # call the stored procedure
        cursor.callproc('publish_tweet', (user_id, content, thread_id))
        
        # get result
        post_id = None
        for result in cursor.stored_results():
            post_id = result.fetchone()[0]
        
        # Extract hashtags manually if trigger failed
        hashtags = [word[1:] for word in content.split() if word.startswith('#')]
        for hashtag in hashtags:
            # Clean hashtag
            hashtag = ''.join(c for c in hashtag if c.isalnum() or c == '_')
            if hashtag:
                # Insert hashtag if it doesn't exist
                cursor.execute(
                    'INSERT IGNORE INTO hashtag (name) VALUES (%s)',
                    (hashtag,)
                )
                # Get hashtag id
                cursor.execute(
                    'SELECT hashtag_id FROM hashtag WHERE name = %s',
                    (hashtag,)
                )
                hashtag_id = cursor.fetchone()[0]
                # Link post to hashtag
                cursor.execute(
                    'INSERT IGNORE INTO contains (post_id, hashtag_id) VALUES (%s, %s)',
                    (post_id, hashtag_id)
                )
        
        conn.commit()
        return post_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# search tweets by hashtag
# stbh - search tweets by hashtag
def search_tweets_by_hashtag(hashtag: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count,
           (SELECT COUNT(*) FROM replies WHERE post_id = p.post_id) as reply_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           JOIN contains c ON p.post_id = c.post_id
           JOIN hashtag h ON c.hashtag_id = h.hashtag_id
           WHERE LOWER(h.name) = LOWER(%s)
           ORDER BY p.created_at DESC''',
        (hashtag,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# search users
# su - search users
def search_users(query: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT user_id, username, email, bio, profile_pic
           FROM user
           WHERE LOWER(username) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s)
           LIMIT 20''',
        (f'%{query}%', f'%{query}%')
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

# search tweets by content
# stbc - search tweets by content
def search_tweets_by_content(query: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT p.post_id as id, p.user_id as user_id, u.username as username, 
           p.content, p.created_at, p.thread_id,
           (SELECT COUNT(*) FROM likes WHERE post_id = p.post_id) as like_count,
           (SELECT COUNT(*) FROM replies WHERE post_id = p.post_id) as reply_count
           FROM post p
           JOIN user u ON p.user_id = u.user_id
           WHERE LOWER(p.content) LIKE LOWER(%s)
           ORDER BY p.created_at DESC''',
        (f'%{query}%',)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# follow a user
# fau - follow a user
def follow_user(follower_id: str, following_id: str) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the stored procedure
    cursor.callproc('follow_user', (follower_id, following_id))
    
    # get result
    success = False
    for result in cursor.stored_results():
        success = bool(result.fetchone()[0])
    
    conn.commit()
    cursor.close()
    conn.close()
    return success

# unfollow a user
# uau - unfollow a user
def unfollow_user(follower_id: str, following_id: str) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the stored procedure
    cursor.callproc('unfollow_user', (follower_id, following_id))
    
    # get result
    success = False
    for result in cursor.stored_results():
        success = bool(result.fetchone()[0])
    
    conn.commit()
    cursor.close()
    conn.close()
    return success

# like a post
# lap - like a post
def like_post(user_id: str, post_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the stored procedure
    cursor.callproc('like_post', (user_id, post_id))
    
    # get result
    success = False
    for result in cursor.stored_results():
        success = bool(result.fetchone()[0])
    
    conn.commit()
    cursor.close()
    conn.close()
    return success

# unlike a post 
# ulp - unlike a post
def unlike_post(user_id: str, post_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the stored procedure
    cursor.callproc('unlike_post', (user_id, post_id))
    
    # get result
    success = False
    for result in cursor.stored_results():
        success = bool(result.fetchone()[0])
    
    conn.commit()
    cursor.close()
    conn.close()
    return success

# check if liked
# cil - check if liked
def is_post_liked(user_id: str, post_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT EXISTS(SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s)',
        (user_id, post_id)
    )
    is_liked = bool(cursor.fetchone()[0])
    
    cursor.close()
    conn.close()
    return is_liked

# get followers
# gf - get followers
def get_followers(user_id: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        '''SELECT u.user_id, u.username, u.bio, u.profile_pic
           FROM follows f
           JOIN user u ON f.follower_id = u.user_id
           WHERE f.following_id = %s''',
        (user_id,)
    )
    
    followers = cursor.fetchall()
    cursor.close()
    conn.close()
    return followers

# get following
# gfg - get following
def get_following(user_id: str) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        '''SELECT u.user_id, u.username, u.bio, u.profile_pic
           FROM follows f
           JOIN user u ON f.following_id = u.user_id
           WHERE f.follower_id = %s''',
        (user_id,)
    )
    
    following = cursor.fetchall()
    cursor.close()
    conn.close()
    return following

# get follower count
# gfc - get follower count
def get_follower_count(user_id: str) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the function
    cursor.execute(f"SELECT get_follower_count(%s)", (user_id,))
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return count

# get following count
# gfgc - get following count
def get_following_count(user_id: str) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the function
    cursor.execute(f"SELECT get_following_count(%s)", (user_id,))
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return count

# check if following
# cif - check if following
def is_following(follower_id: str, following_id: str) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the function
    cursor.execute(f"SELECT check_if_following(%s, %s)", (follower_id, following_id))
    is_following = bool(cursor.fetchone()[0])
    
    cursor.close()
    conn.close()
    return is_following
