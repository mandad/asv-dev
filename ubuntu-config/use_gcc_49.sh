sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-get install g++-4.9

sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.9 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 50
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.9 100
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 50
sudo update-alternatives --install /usr/bin/cpp cpp-bin /usr/bin/cpp-4.9 100
sudo update-alternatives --install /usr/bin/cpp cpp-bin /usr/bin/cpp-4.8 50
