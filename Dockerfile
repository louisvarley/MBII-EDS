FROM ubuntu
MAINTAINER Baris Sencan <baris.sncn@gmail.com>

# Expose a range of possible Jedi Academy ports.
EXPOSE 29060-29062/udp 29070-29081/udp

# Install dependencies.
#RUN yum install -y --allowerasing glibc.i686
#RUN yum install -y --allowerasing libcurl.i686



# Mount game data volume.
VOLUME /opt/openjk/MBII
VOLUME /opt/openjk/base

# Copy server files.

# Base Files
COPY server/base/cgamex86_64.so /root/.local/share/openjk/base/
COPY server/base/jampgamex86_64.so /root/.local/share/openjk/base/
COPY server/base/uix86_64.so /root/.local/share/openjk/base/
COPY server/base/jampgamex86_64.so /root/.local/share/openjk/base/

# Lib Files






COPY server/rdsp-vanilla_x86_64.so /usr/lib/rdsp-vanilla.so
COPY server/rd-vanilla_x86_64.so /usr/lib/rd-vanilla.so

# OpenJK Files
COPY server/OpenJK/cgamex86_64.so /opt/openjk/cgamex86_64.so
COPY server/OpenJK/jagamex86_64.so /opt/openjk/jagamex86_64.so
COPY server/OpenJK/jampgamex86_64.so /opt/openjk/jampgamex86_64.so
COPY server/OpenJK/uix86_64.so /opt/openjk/uix86_64.so

# Binaries
COPY server/openjkded.x86_64 /usr/bin/openjkded


# Scripts
COPY server/rtvrtm.py /opt/rtvrtm/rtvrtm.py
COPY server/start.sh /opt/openjk/start.sh


# Set the working directory to where the Jedi Academy data files will be
# mounted at, so that linuxjampded finds them.

WORKDIR /opt/openjk

# Start the server.

RUN chmod +x /usr/bin/openjkded
RUN chmod +x /opt/openjk/start.sh

CMD ["/opt/openjk/start.sh"]



#CMD ["openjkded"]


