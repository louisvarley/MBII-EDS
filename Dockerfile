FROM ubuntu
MAINTAINER Baris Sencan <baris.sncn@gmail.com>

# Expose a range of possible Jedi Academy ports.
EXPOSE 29060-29062/udp 29070-29081/udp

# 32bit Arch
RUN dpkg --add-architecture i386

# Install dependencies.
RUN apt-get update 
RUN apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386
RUN apt-get install -y zlib1g:i386 
RUN apt-get install -y curl:i386 
RUN apt-get install -y python-setuptools python-dev 
RUN apt-get install -y net-tools
RUN apt-get install -y fping

# Mount game data volume.
VOLUME /opt/openjk/MBII
VOLUME /opt/openjk/base
VOLUME /opt/openjk/configs

# Base Files
COPY server/base/* /root/.local/share/openjk/base/

# LIB Files
COPY server/rd-vanilla_i386.so /usr/lib/

# OpenJK Files
COPY server/OpenJK/* /opt/openjk/

# Binaries
#COPY server/openjkded.i386 /usr/bin/openjkded
#COPY server/mbiided.i386 /usr/bin/mbiided
COPY server/*.i386 /usr/bin/

COPY server/OpenJK/jampgamei386.so /root/.local/share/openjk/MBII/jampgamei386.so

# Scripts
COPY server/rtvrtm.py /opt/rtvrtm/rtvrtm.py
COPY server/start.sh /opt/openjk/start.sh

# Set the working directory to where the Jedi Academy data files will be
# mounted at, so that linuxjampded finds them.

WORKDIR /opt/openjk

# Start the server.

#RUN chmod +x /usr/bin/openjkded
#RUN chmod +x /usr/bin/mbiided
RUN chmod +x /usr/bin/*.i386
RUN chmod +x /opt/openjk/start.sh

CMD ["/opt/openjk/start.sh"]



