#Install MOOS-IvP on Ubuntu
sudo apt-get -y install subversion git vim
cd ~/
mkdir code
cd code

#clone in code
git clone https://github.com/wjwwood/serial.git
git clone https://github.com/mandad/python-moos.git
git clone https://github.com/mandad/asv-dev.git
git clone https://github.com/mandad/moos-ivp-manda.git
git clone https://github.com/mandad/essential-moos.git
git clone https://github.com/mandad/core-moos.git
svn co https://oceanai.mit.edu/svn/moos-ivp-aro/trunk/ moos-ivp

#copy patches
cp essential-moos/Essentials/pLogger/MOOSLogger.* moos-ivp/MOOS/MOOSEssentials/Essentials/pLogger/
cp core-moos/Core/libMOOS/Comms/ThreadedCommServer.cpp moos-ivp/MOOS/MOOSCore/Core/libMOOS/Comms/
#need to add other coremods

#Code dependencies
sudo apt-get -y install g++ xterm cmake libfltk1.3-dev freeglut3-dev libpng12-dev libjpeg-dev libxft-dev libxinerama-dev libtiff5-dev libproj-dev
sudo apt-get -y install cmake-curses-gui python-dev libboost-all-dev
# My dependencies
sudo apt-get -y install libeigen3-dev libgeos-dev libgeos++-dev

#ROS Stuff
#Only works on <= 15.04
CODENAME=$(lsb_release -sc)
if [ CODENAME != "wily" ]; then
    sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
    sudo apt-key adv --keyserver hkp://ha.pool.sks-keyservers.net:80 --recv-key 0xB01FA116
    sudo apt-get update
    sudo apt-get install -y ros-jade-catkin
    echo "source /opt/ros/jade/setup.bash" > setup.bash
else # Install from source on 15.10 (wily)
    sudo apt-get -y install python-empy python-nose python-setuptools libgtest-dev python-pip
    pip install catkin_pkg
    git clone https://github.com/ros/catkin.git
    cd catkin/
    mkdir build && cd build && cmake ../ && make && sudo make install
    cd ../../
fi

#Build MOOS-IvP & pymoos
cd moos-ivp/
sh build-moos.sh
sh build-ivp.sh
cd ~/code/python-moos/
mkdir build && cd build && cmake ../ && make
cp lib/pymoos.so ~/code/asv-dev/utilities/python_moosapps/

#Build serial library
cd ~/code/serial/
make && make install
sudo cp -r /tmp/usr/local/* /usr/local/

#Build my MOOS extensions
#ln -s ~/code/asv-dev/moos-ivp-emily/ ~/code/moos-ivp-emily
cd ~/code/moos-ivp-manda
mkdir build && ./build.sh
echo "PATH=\$PATH:~/code/moos-ivp/bin:~/code/moos-ivp-manda/bin" >> ~/.bashrc

#Some extra configuration
git config --global user.email "damian.manda@noaa.gov"
git config --global user.name "Damian Manda"
git config --global push.default simple
