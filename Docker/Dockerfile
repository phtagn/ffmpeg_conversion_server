FROM alpine:latest

# Install build deps

ARG        PKG_CONFIG_PATH=/usr/lib/pkgconfig
ARG        LD_LIBRARY_PATH=/usr/lib
ARG        PREFIX=/usr
ARG        MAKEFLAGS="-j12"
ENV        PATH $PATH:/conversion-server/conversion-server
ENV 	   WATCHFOLDER='/downloads/watchfolder'
ENV        SERVER_PORT='7080'
ENV        PUID='911'
ENV        PGID='1000'
ENV        GITSERVER='https://github.com/phtagn/ffmpeg_conversion_server.git'
ENV        AUTOUPDATE='true'
ENV        GITBRANCH='server-develop'
ENV        FLASK_APP='conversion-server'
ENV        FLASK_ENV='development'

#RUN apk add --no-cache --update \
#	libgcc \
#	libstdc++ \
#	ca-certificates \
#	libcrypto1.0 \
#	libssl1.0 \
#	libgomp \
#	expat \
#	autoconf \
#	automake \
#	binutils \
#	bzip2 \
#	cmake \
#	coreutils \
#	file \
#	g++ \
#	gcc \
#	gperf \
#	git \
#	libtool \
#	make \
#	python3 \
#	openssl-dev \
#	tar \
#	yasm \
#	zlib-dev \
#	expat-dev \
#	py3-pip \
#	texinfo \
#	diffutils \
#	curl \
#	mercurial


RUN apk add --no-cache --update \
python3 \
py3-pip \
git \
bash

WORKDIR /tmp




ADD https://github.com/just-containers/s6-overlay/releases/download/v1.21.4.0/s6-overlay-amd64.tar.gz /tmp/
RUN tar xzf /tmp/s6-overlay-amd64.tar.gz -C /

RUN \
    apk add --no-cache shadow && \
	groupmod -g ${PGID} users && \
	useradd -u ${PUID} -U -d /config -s /bin/false abc && \
	usermod -G users abc && \
	mkdir -p /config

RUN mkdir /conversion-server
COPY ffmpeg_conversion_server/ /conversion-server

COPY ffmpeg_conversion_server/Docker/rootfs/ /


RUN \
	rm -Rf /tmp/*

#RUN apk del \
#	autoconf \
#	automake \
#	binutils \
#	cmake \
#	g++ \
#	gcc \
#	gperf \
#	make \
#	openssl-dev \
#	yasm \
#	texinfo \
#	diffutils \
#	mercurial

RUN pip3 install --upgrade pip


WORKDIR /conversion-server
EXPOSE 5000
ENTRYPOINT  ["/init"]
