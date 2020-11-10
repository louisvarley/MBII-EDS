FROM centos
MAINTAINER Baris Sencan <baris.sncn@gmail.com>

# Expose a range of possible Jedi Academy ports.
EXPOSE 29060-29062/udp 29070-29081/udp

# Install dependencies.
RUN yum install -y --allowerasing glibc.i686
RUN yum install -y --allowerasing libcurl.i686

# Copy server files.

COPY server/rdsp-vanilla_i386.so /usr/lib/rdsp-vanilla_i386.so
COPY server/rd-vanilla_i386.so /usr/lib/rd-vanilla_i386.so
COPY server/rtvrtm.py /opt/rtvrtm/rtvrtm.py
COPY server/openjkded /opt/openjk/openjkded
COPY server/start.sh /opt/openjk/start.sh


# Mount game data volume.
VOLUME /jedi-academy

# Set the working directory to where the Jedi Academy data files will be
# mounted at, so that linuxjampded finds them.
WORKDIR /jedi-academy

# Start the server.
CMD ["/opt/openjk/start.sh"]
