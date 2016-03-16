FROM centos
MAINTAINER Baris Sencan <baris.sncn@gmail.com>

# Expose Jedi Academy ports.
EXPOSE 29060-29062/udp 29070-29081/udp

# Install dependencies.
RUN yum install -y glibc.i686
RUN yum install -y screen

# Copy server files.
COPY server/libcxa.so.1 /usr/lib/libcxa.so.1
COPY server/linuxjampded /opt/ja-server/linuxjampded
COPY server/jampgamei386.so /opt/ja-server/jampgamei386.so
COPY server/start.sh /opt/ja-server/start.sh

# Mount game data volume and link server configuration file.
VOLUME /jedi-academy
RUN mkdir -p /root/.ja/base
RUN ln -s /jedi-academy/server.cfg /root/.ja/base/server.cfg

# Set the working directory to where the Jedi Academy data files will be
# mounted at, so that linuxjampded finds them.
WORKDIR /jedi-academy

# Start the server in a new screen.
CMD ["screen", "-S", "ja"]
CMD ["/opt/ja-server/start.sh"]
