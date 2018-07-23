#!/bin/bash


# This script installs zeeguu on a freshly installed OS X 
# It has been tested on OS X 10.13 - High Sierra

# It assumes homebrew and xcode command line toos
# that you can install with
# install homebrew
# xcode-select --install


# folder to install the virtual env. 
# feel free to change this
VIRTENVDIR=~/.venvs

# name of the zeeguu virtual env
# feel free to change
ZENV=z_env


echo "# 1. Install all the prerequisite mac packges..."
brew install mysql
brew services start mysql #start mysql at login



echo "# 2. Install Python 3 if not present already"

if which python3 ; then
    echo "Python3 detected. Will continue without installing"
else
	echo "Installing Python3.X"

	brew install python

fi

echo "# 3. Create new virtual enviroment"

mkdir $VIRTENVDIR
python3 -m venv $VIRTENVDIR/$ZENV
source $VIRTENVDIR/$ZENV/bin/activate


echo "# 4. Install several of the prerequisites, the others will be installed based on setup.py"

pip3 install mysqlclient
pip3 install -r requirements.txt



echo "# 5. Run setup to install the final prerequisites "

python3 setup.py develop


echo "# 6. Ensure that all went well by running the tests"

./run_tests.sh


echo "echo  " > activate_zeeguu.sh
echo "echo Always activate the zeeguu environment with the following line" >> activate_zeeguu.sh
echo "echo  " >> activate_zeeguu.sh
echo "echo '    source $VIRTENVDIR/$ZENV/bin/activate'" >> activate_zeeguu.sh
echo "echo  " >> activate_zeeguu.sh
echo "echo As a reminder call this script from the current folder" >> activate_zeeguu.sh
echo "echo  " >> activate_zeeguu.sh
echo "echo '   ./activate_zeeguu.sh'" >> activate_zeeguu.sh
echo "echo " >> activate_zeeguu.sh

chmod +x activate_zeeguu.sh

./activate_zeeguu.sh







