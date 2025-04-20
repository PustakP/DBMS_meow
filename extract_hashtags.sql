-- Extract hashtags from existing posts and insert them into hashtag and contains tables
DELIMITER //

CREATE PROCEDURE extract_hashtags_from_posts()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE post_id INT;
    DECLARE content TEXT;
    DECLARE cur CURSOR FOR SELECT post_id, content FROM post;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO post_id, content;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Extract hashtags using regex
        SET @pos = 1;
        WHILE @pos > 0 DO
            SET @pos = LOCATE('#', content, @pos);
            IF @pos > 0 THEN
                SET @end = LOCATE(' ', content, @pos);
                IF @end = 0 THEN
                    SET @end = LENGTH(content) + 1;
                END IF;
                
                SET @hashtag = SUBSTRING(content, @pos + 1, @end - @pos - 1);
                
                -- Insert hashtag if it doesn't exist
                INSERT IGNORE INTO hashtag (name) VALUES (@hashtag);
                
                -- Get hashtag_id
                SET @hashtag_id = (SELECT hashtag_id FROM hashtag WHERE name = @hashtag);
                
                -- Insert into contains table
                INSERT IGNORE INTO contains (post_id, hashtag_id) VALUES (post_id, @hashtag_id);
                
                SET @pos = @end;
            END IF;
        END WHILE;
    END LOOP;
    
    CLOSE cur;
END //

DELIMITER ;

-- Execute the procedure
CALL extract_hashtags_from_posts();

-- Clean up
DROP PROCEDURE IF EXISTS extract_hashtags_from_posts; 