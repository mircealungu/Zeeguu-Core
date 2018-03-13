# Zeeguu-Core 
[![Build Status](https://travis-ci.org/zeeguu-ecosystem/Zeeguu-Core.svg?branch=master)](https://travis-ci.org/zeeguu-ecosystem/Zeeguu-Core) 
[![Coverage Status](https://coveralls.io/repos/github/zeeguu-ecosystem/Zeeguu-Core/badge.svg?branch=master)](https://coveralls.io/github/zeeguu-ecosystem/Zeeguu-Core?branch=master)

The main model behind the zeeguu infrastructure.


# Installation

Clone this repo

For installing on a fresh Ubuntu (10.04) run the `./ubuntu_install.sh` script.
For other OSs take inspiration from that file, but skipping step 1. 

To be able to do anything meaningful with the Zeeguu-Core 
you must set the environment variable `ZEEGUU_CORE_CONFIG` 
to the path of a file which contains the info that's 
declared in `testing_default.cfg`. 

Only if you have defined the previous envvar can you start
working with zeeguu model elements by importing `zeeguu.model`. 



<!-- # Setup for Local Testing
6. Run `mysql -u root -p`
   1. Run `CREATE DATABASE zeeguu;`
   2. Run `exit`
6. Run `mysql.server start`
9. (Optional) You can populate the DB with the dataset that we used for the [CHI paper](https://github.com/zeeguu-ecosystem/CHI18-Paper/)
   1. download the [anonymized database dump](https://github.com/zeeguu-ecosystem/CHI18-Paper/blob/master/data/chi18_dataset_anon_2018-01-15.sql.zip) and unzip the file
   1. mysql -u root -p zeeguu < chi18_dataset_anon_2018-01-15.sql
   3. The database *should* be populated by now.
 -->

<!-- # MySQL

Install mysql and also the connection to python
```
apt-get install mysql-server libmysqlclient-dev python-mysqldb
```

# Project dev dependencies
```
apt-get install libxml2-dev libxslt1-dev
```
 -->