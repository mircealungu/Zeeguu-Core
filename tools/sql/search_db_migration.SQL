/** This document applies the changes needed for the search functionality to the 
 ** zeeguu database, be careful. 
 */
 
/** Drop the tables for the old topics which isn't needed anymore */
DROP TABLE article_topic_mapping;
DROP TABLE topic;


/** Optional: apply changes so people can learn more than one language */
CREATE TABLE user_language (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	user_id INT(11),
	language_id INT(11),
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (language_id) REFERENCES language(id) 
); 

/** Create the new tables needed */
/** topic(id,title) */
CREATE TABLE topic ( 
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	title VARCHAR(30) NOT NULL
); 

/** topic_keyword(id,topic_id,language_id,topic_translated,keywords)
		foreign keys for topic_id and language_id */

CREATE TABLE localized_topic (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	topic_id INT(11),
	language_id INT(11),
	topic_translated VARCHAR(30) NOT NULL,
	keywords  VARCHAR(1024) NOT NULL,
	FOREIGN KEY (topic_id) REFERENCES topic(id),
	FOREIGN KEY (language_id) REFERENCES language(id)
);

/** topic_subscription(id,user_id,topic_id)
		foreign keys for user_id and topic_id */
CREATE TABLE topic_subscription (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	user_id INT(11),
	topic_id INT(11),
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (topic_id) REFERENCES topic(id)
);

/** topic_filter(id,user_id,topic_id)
		foreign keys for user_id and topic_id */
CREATE TABLE topic_filter (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	user_id INT(11),
	topic_id INT(11),
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (topic_id) REFERENCES topic(id)
);

/** article_topic_map(id,article_id,topic_id)
		foreign keys for article_id and topic_id */
CREATE TABLE article_topic_map (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	article_id INT(11),
	topic_id INT(11),
	FOREIGN KEY (article_id) REFERENCES article(id),
	FOREIGN KEY (topic_id) REFERENCES topic(id)
);

/** search(id,keywords) */
CREATE TABLE search (
	id INT(6) AUTO_INCREMENT PRIMARY KEY,
	keywords VARCHAR(100)
);

/** article_search_map(id,article_id,topic_id)
		foreign keys for article_id and topic_id */
CREATE TABLE article_search_map (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	article_id INT(11),
	search_id INT(11),
	FOREIGN KEY (article_id) REFERENCES article(id),
	FOREIGN KEY (search_id) REFERENCES search(id)
);

/** search_subscription(id,user_id,search)
		foreign key for user_id */
CREATE TABLE search_subscription (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	user_id INT(11),
	search_id INT(11),
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (search_id) REFERENCES search(id)
);

/** search_filter(id,user_id,search)
		foreign key for user_id */
CREATE TABLE search_filter (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	user_id INT(11),
	search_id INT(11),
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (search_id) REFERENCES search(id)
);

/** article_word(id, word) */
CREATE TABLE article_word (
	id INT(11) AUTO_INCREMENT PRIMARY KEY,
	word VARCHAR(30)
);

/** article_word_map(article_id, word_id)
		foreign key for article_id
		foreign key for word_id */
CREATE TABLE article_word_map (
	article_id INT(11),
	word_id INT(11),
	FOREIGN KEY (article_id) REFERENCES article(id),
	FOREIGN KEY (word_id) REFERENCES article_word(id)
);






