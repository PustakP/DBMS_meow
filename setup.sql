-- Database creation
CREATE DATABASE pinkbird;
USE pinkbird;

-- User Table
CREATE TABLE user (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    bio TEXT,
    profile_pic VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS user_auth (user_id VARCHAR(36), password_hash VARCHAR(255), PRIMARY KEY (user_id), FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE);

-- Post Table
CREATE TABLE post (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thread_id INT,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (thread_id) REFERENCES post(post_id) ON DELETE CASCADE
);

-- Hashtag Table
CREATE TABLE hashtag (
    hashtag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Media Table
CREATE TABLE media (
    media_id INT AUTO_INCREMENT PRIMARY KEY,
    file_url VARCHAR(255) NOT NULL,
    media_type VARCHAR(50) NOT NULL
);

-- Follows Table
CREATE TABLE follows (
    follower_id VARCHAR(36),
    following_id VARCHAR(36),
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Likes Table
CREATE TABLE likes (
    user_id VARCHAR(36),
    post_id INT,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES post(post_id) ON DELETE CASCADE
);

-- Replies Table
CREATE TABLE replies (
    post_id INT,
    reply_id INT,
    PRIMARY KEY (post_id, reply_id),
    FOREIGN KEY (post_id) REFERENCES post(post_id) ON DELETE CASCADE,
    FOREIGN KEY (reply_id) REFERENCES post(post_id) ON DELETE CASCADE
);

-- Contains Table
CREATE TABLE contains (
    post_id INT,
    hashtag_id INT,
    PRIMARY KEY (post_id, hashtag_id),
    FOREIGN KEY (post_id) REFERENCES post(post_id) ON DELETE CASCADE,
    FOREIGN KEY (hashtag_id) REFERENCES hashtag(hashtag_id) ON DELETE CASCADE
);

-- Hasmedia Table
CREATE TABLE hasmedia (
    post_id INT,
    media_id INT,
    PRIMARY KEY (post_id, media_id),
    FOREIGN KEY (post_id) REFERENCES post(post_id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media(media_id) ON DELETE CASCADE
);

-- ========================
-- STORED PROCEDURES
-- ========================

-- proc to publish a new tweet
-- pnt - procedure new tweet
DELIMITER //
CREATE PROCEDURE publish_tweet(
    IN p_user_id VARCHAR(36),
    IN p_content TEXT,
    IN p_thread_id INT
)
BEGIN
    DECLARE new_post_id INT;
    
    -- insert new post
    INSERT INTO post (user_id, content, thread_id)
    VALUES (p_user_id, p_content, p_thread_id);
    
    SET new_post_id = LAST_INSERT_ID();
    
    -- if this is a reply to another post, add to replies table
    IF p_thread_id IS NOT NULL THEN
        INSERT INTO replies (post_id, reply_id)
        VALUES (p_thread_id, new_post_id);
    END IF;
    
    -- return the new post id
    SELECT new_post_id AS post_id;
END //
DELIMITER ;

-- proc to follow a user
-- pfu - procedure follow user
DELIMITER //
CREATE PROCEDURE follow_user(
    IN p_follower_id VARCHAR(36),
    IN p_following_id VARCHAR(36)
)
BEGIN
    -- check if already following
    IF NOT EXISTS (
        SELECT 1 FROM follows 
        WHERE follower_id = p_follower_id AND following_id = p_following_id
    ) THEN
        -- insert follow relationship
        INSERT INTO follows (follower_id, following_id)
        VALUES (p_follower_id, p_following_id);
        
        SELECT TRUE AS success;
    ELSE
        SELECT FALSE AS success;
    END IF;
END //
DELIMITER ;

-- proc to unfollow a user
-- puu - procedure unfollow user
DELIMITER //
CREATE PROCEDURE unfollow_user(
    IN p_follower_id VARCHAR(36),
    IN p_following_id VARCHAR(36)
)
BEGIN
    -- delete follow relationship
    DELETE FROM follows 
    WHERE follower_id = p_follower_id AND following_id = p_following_id;
    
    IF ROW_COUNT() > 0 THEN
        SELECT TRUE AS success;
    ELSE
        SELECT FALSE AS success;
    END IF;
END //
DELIMITER ;

-- proc to like a post
-- plp - procedure like post
DELIMITER //
CREATE PROCEDURE like_post(
    IN p_user_id VARCHAR(36),
    IN p_post_id INT
)
BEGIN
    -- check if already liked
    IF NOT EXISTS (
        SELECT 1 FROM likes 
        WHERE user_id = p_user_id AND post_id = p_post_id
    ) THEN
        -- insert like
        INSERT INTO likes (user_id, post_id)
        VALUES (p_user_id, p_post_id);
        
        SELECT TRUE AS success;
    ELSE
        SELECT FALSE AS success;
    END IF;
END //
DELIMITER ;

-- proc to unlike a post
-- pup - procedure unlike post 
DELIMITER //
CREATE PROCEDURE unlike_post(
    IN p_user_id VARCHAR(36),
    IN p_post_id INT
)
BEGIN
    -- delete like
    DELETE FROM likes 
    WHERE user_id = p_user_id AND post_id = p_post_id;
    
    IF ROW_COUNT() > 0 THEN
        SELECT TRUE AS success;
    ELSE
        SELECT FALSE AS success;
    END IF;
END //
DELIMITER ;

-- proc to create a user
-- pcu - procedure create user
DELIMITER //
CREATE PROCEDURE create_user(
    IN p_user_id VARCHAR(36),
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_bio TEXT,
    IN p_profile_pic VARCHAR(255)
)
BEGIN
    -- check if username or email already exists
    IF EXISTS (
        SELECT 1 FROM user 
        WHERE username = p_username OR email = p_email
    ) THEN
        SELECT FALSE AS success, 'Username or email already exists' AS message;
    ELSE
        -- insert new user
        INSERT INTO user (user_id, username, email, bio, profile_pic)
        VALUES (p_user_id, p_username, p_email, p_bio, p_profile_pic);
        
        SELECT TRUE AS success, 'User created successfully' AS message;
    END IF;
END //
DELIMITER ;

-- ========================
-- FUNCTIONS
-- ========================

-- func to get follower count
-- gfc - get follower count
DELIMITER //
CREATE FUNCTION get_follower_count(p_user_id VARCHAR(36)) 
RETURNS INT DETERMINISTIC
BEGIN
    DECLARE follower_count INT;
    
    SELECT COUNT(*) INTO follower_count
    FROM follows
    WHERE following_id = p_user_id;
    
    RETURN follower_count;
END //
DELIMITER ;

-- func to get following count
-- gfg - get following count
DELIMITER //
CREATE FUNCTION get_following_count(p_user_id VARCHAR(36)) 
RETURNS INT DETERMINISTIC
BEGIN
    DECLARE following_count INT;
    
    SELECT COUNT(*) INTO following_count
    FROM follows
    WHERE follower_id = p_user_id;
    
    RETURN following_count;
END //
DELIMITER ;

-- func to get post like count
-- gpl - get post likes
DELIMITER //
CREATE FUNCTION get_post_likes_count(p_post_id INT) 
RETURNS INT DETERMINISTIC
BEGIN
    DECLARE likes_count INT;
    
    SELECT COUNT(*) INTO likes_count
    FROM likes
    WHERE post_id = p_post_id;
    
    RETURN likes_count;
END //
DELIMITER ;

-- func to check if user follows another
-- cif - check if following
DELIMITER //
CREATE FUNCTION check_if_following(p_follower_id VARCHAR(36), p_following_id VARCHAR(36)) 
RETURNS BOOLEAN DETERMINISTIC
BEGIN
    DECLARE is_following BOOLEAN;
    
    SELECT EXISTS (
        SELECT 1 FROM follows 
        WHERE follower_id = p_follower_id AND following_id = p_following_id
    ) INTO is_following;
    
    RETURN is_following;
END //
DELIMITER ;

-- ========================
-- TRIGGERS
-- ========================

-- trigger to extract hashtags from post content
-- eht - extract hashtags trigger
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

-- Sample Data Insertions
INSERT INTO user (user_id, username, email, bio, profile_pic) VALUES
('123', 'Nishitai3', 'nishita@gmail.com', 'i love coffee', 'pic123.jpg'),
('564', 'pustak_alt', 'pustak@gmail.com', 'i make pasta', 'pic564.jpg');

-- Using AUTO_INCREMENT for post_id now
INSERT INTO post (user_id, content, created_at, thread_id) VALUES
('123', 'found an amazing coffee place near work! #coffee', '2025-04-01 23:05:06', NULL),
('564', 'trying a new recipe, hope it turns out good #recipe', '2025-04-01 23:06:49', NULL),
('564', 'recommend good cooking #books please #recipe', '2025-04-01 23:22:44', NULL),
('564', 'that coffee place is my favorite too! #coffee', '2025-04-01 23:26:53', 1),
('123', 'let me know how your recipe turns out! #recipe #books', '2025-04-01 23:26:53', 2);

-- The hashtag table will be populated by trigger
-- Contains table will be filled by trigger

INSERT INTO media (file_url, media_type) VALUES
('coffee_shop.jpg', 'image'),
('recipe_video.mp4', 'video');

INSERT INTO follows (follower_id, following_id) VALUES
('123', '564');

INSERT INTO likes (user_id, post_id) VALUES
('123', 3),
('564', 1);

INSERT INTO hasmedia (post_id, media_id) VALUES
(1, 1), (2, 2);


