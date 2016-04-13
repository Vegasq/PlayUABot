# Set the base image to use to Ubuntu
FROM ubuntu:14.04

# Set the file maintainer (your name - the file's author)
MAINTAINER Mykola Yakovliev

# Set env variables used in this Dockerfile (add a unique prefix, such as DOCKYARD)
# Local directory with project source
ENV DOCKYARD_SRC=.

# Directory in container for all project files
ENV DOCKYARD_SRVHOME=/opt

# Directory in container for project source files
ENV DOCKYARD_SRVPROJ=/opt/playuabot

# Update the default application repository sources list
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python3 python3-pip python3-dev git

# Copy application source code to SRCDIR
COPY $DOCKYARD_SRC $DOCKYARD_SRVPROJ

COPY playua.cfg /etc/playua.cfg

# Install Python dependencies
RUN mkdir ~/.ssh/
RUN ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
RUN pip3 install -r $DOCKYARD_SRVPROJ/requirements.txt
RUN chmod +x /opt/playuabot/bot.py

WORKDIR /opt/
RUN git clone https://github.com/patx/pickledb.git
WORKDIR /opt/pickledb
RUN git fetch origin pull/13/head:fixedpy3
RUN git checkout fixedpy3
RUN pip3 install -e . -U

VOLUME /playuadb

ENTRYPOINT ["/opt/playuabot/bot.py"]

