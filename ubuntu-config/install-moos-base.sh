#Install MOOS-IvP on Ubuntu
sudo apt-get -y install subversion git vim
cd ~/
mkdir code
cd code

#clone in code
git clone https://github.com/mandad/python-moos.git
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

#Build MOOS-IvP & pymoos
cd moos-ivp/
sh build-moos.sh
sh build-ivp.sh
cd ~/code/python-moos/
mkdir build && cd build && cmake ../ && make

echo "PATH=\$PATH:~/code/moos-ivp/bin" >> ~/.bashrc
