#!/bin/bash


# This script installs zeeguu on a freshly installed Ubuntu 
# It has been tested on Ubuntu 10.04


# folder to install the virtual env. 
# feel free to change this
VIRTENVDIR=~/.venvs

# name of the zeeguu virtual env
# feel free to change
ZENV=zenv


echo "# 1. install all the prerequisite ubuntu packges"

sudo apt-get update
sudo apt-get install -y build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libmysqlclient-dev mysql-client-core-5.7 mysql-server libmysqlclient-dev python-mysqldb


echo "# 2. download and install Python from sources if not present already"

if which python3.6 ; then
    echo "Python3.6 detected. Will continue without installing"
else
	echo "Installing Python3.6 from sources."

	wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz

	tar xvf Python-3.6.3.tar.xz

	cd Python-3.6.3/

	./configure

	sudo make altinstall

fi

echo "#3. create new virtual enviroment"

mkdir $VIRTENVDIR
python3.6 -m venv $VIRTENVDIR/$ZENV
source $VIRTENVDIR/$ZENV/bin/activate


echo "4. install several of the prerequisites, the others will be installed based on setup.py"

pip install jieba3k lxml Pillow nltk pytest



echo "# 5. run setup to install the final prerequisites "

python3.6 setup.py develop


echo "6. make sure that the installation is ok by running the tests"

./run_tests.sh


echo "Always activate the zeeguu environment with the following line" 
echo " "
echo "    source $VIRTENVDIR/$ZENV/bin/activate"







