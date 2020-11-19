!#bin/sh

docker pull bsencan/jedi-academy-server
sudo apt-get install make -y
sudo apt-get install python3-pip -y
pip3 install docker
pip3 install psutil
make
ln -s /root/mbii-eds/mbii.py /usr/bin/mbii
