!#bin/sh

docker pull bsencan/jedi-academy-server
sudo apt-get install make -y
sudo apt-get install python3-pip -y
pip3 install docker
make
ln -s /root/mbii-eds/mbii.py /usr/bin/mbii
