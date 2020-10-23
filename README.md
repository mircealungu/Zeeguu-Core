# Zeeguu-Core

[![Build Status](https://travis-ci.org/zeeguu-ecosystem/Zeeguu-Core.svg?branch=master)](https://travis-ci.org/zeeguu-ecosystem/Zeeguu-Core) 
[![Coverage Status](https://coveralls.io/repos/github/zeeguu-ecosystem/Zeeguu-Core/badge.svg?branch=master)](https://coveralls.io/github/zeeguu-ecosystem/Zeeguu-Core?branch=master)

The main model behind the zeeguu infrastructure.


# Installation

For installing on a fresh Ubuntu (16.04) run the `./ubuntu_install.sh` script.

For other OSs take inspiration from the aforementioned file, but skipping step 1. 

To be able to do anything meaningful with the Zeeguu-Core 
you must set the environment variable `ZEEGUU_CORE_CONFIG` 
to the path of a file which contains the info that's 
declared in `testing_default.cfg`. Only then can you start
working with zeeguu model elements by importing `zeeguu.model`. 

# Installing on Windows

1. git clone https://github.com/zeeguu-ecosystem/Zeeguu-Core.git
1. python -m venv zenv 
1. #activate the new enviroment by running ./zenv/bin/activate (on Mac/Linux) oir .\zenv\Scripts\activate.bat (on Win)
1. cd Zeeguu-Core
1. pip install -r requirements.txt
1. python -c "import nltk; nltk.download('punkt')"
1. python -m pytest

# Installing on Mac (Notes)
If you get an error like this: 

    ld: library not found for -lssl
    
when installing mysqlclient try to: 

    brew install openssl
    env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pip install mysqlclient
    
this is cf. https://stackoverflow.com/a/51701291/1200070

# Setting up ElasticSearch 7.6.2 (Mac / Linux)

Follow instructions on: 
  https://www.elastic.co/guide/en/elasticsearch/reference/current/targz.html

Install on localhost for test (127.0.0.1:9200)

When installing, we recommend at least 4 GB dedicated to ElasticSearch. This can easily support querying of 30+ concurrent users. If it is a single node cluster (one server), we recommend the node to both be able to ingest, hold data and be master. The two latter needs to be enabled. 

To export data from MySQL to ElasticSearch run zeeguu_core/tools/mysql_to_elastic.py. 
Please notice that the name of the index is placed in the settings.py located in zeeguu_core/Elastic.

This process takes approximately 1.5h for 1 million articles.

Afterwards, please check that you can access the data on the following ip/port:
http://127.0.0.1:9200/{index_name}/_doc/{id}

Now you should be able to query with full text search through ElasticSearch.
