FROM ubuntu:22.04

##########################
# INSTALL OS DEPENDENCIES
##########################
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y \
    apt-utils \
    autoconf \
    bison \
    flex \
    gcc \
    libc6-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libncurses5 \
    libncurses5-dev \
    libpcre3-dev \
    libreadline8 \
    libreadline-dev \
    make \
    pkg-config \
    subversion \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    cython3 \
    wget \
    tar \
    gzip \
    less \
    openssh-client \
    mg

########################
# INSTALL PYTHON PIPENV
########################
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -q pipenv

##############################
# INSTALL CWB DEBIAN PACKAGES
##############################
RUN wget https://kumisystems.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb_3.5.0-1_amd64.deb
RUN wget https://master.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb-dev_3.5.0-1_amd64.deb
RUN apt-get install ./cwb_3.5.0-1_amd64.deb
RUN apt-get install ./cwb-dev_3.5.0-1_amd64.deb

######################
# INSTALL SPHEROSCOPE
######################
RUN git clone https://github.com/ausgerechnet/spheroscope.git /spheroscope
WORKDIR /spheroscope
COPY cfg_example.py 
RUN make install
RUN make init && make library
RUN make run
