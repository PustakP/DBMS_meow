import mysql.connector
from typing import List, Dict

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

# get all tweets from db
# gat - get all tweets
def get_all_tweets() -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT post_id as id, user_id as user, content, created_at FROM post ORDER BY created_at DESC'
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# publish new tweet
# pnt - publish new tweet
def publish_tweet(user: str, content: str, thread_id: int = None) -> None:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the stored procedure
    cursor.callproc('publish_tweet', (user, content, thread_id))
    
    # get result
    for result in cursor.stored_results():
        post_id = result.fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()
    return post_id

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

# get follower count
# gfc - get follower count
def get_follower_count(user_id: str) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    
    # call the function
    cursor.execute(f"SELECT get_follower_count('{user_id}')")
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
    cursor.execute(f"SELECT get_following_count('{user_id}')")
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
    cursor.execute(f"SELECT check_if_following('{follower_id}', '{following_id}')")
    is_following = bool(cursor.fetchone()[0])
    
    cursor.close()
    conn.close()
    return is_following
