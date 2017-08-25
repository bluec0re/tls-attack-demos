FROM debian

RUN apt-get update && apt-get install -y build-essential zlib1g-dev screen pkg-config \
    && apt-get remove -y libssl1.1 \
    && rm -rf /var/lib/apt/lists/*

# last heartbleed version
#RUN curl https://www.openssl.org/source/old/1.0.1/openssl-1.0.1f.tar.gz -o openssl.tar.gz
COPY openssl.tar.gz /openssl.tar.gz
RUN tar xvf openssl.tar.gz && \
    cd openssl-1.0.1f && \
    CFLAGS="-fPIC" ./config -Wl,-rpath=/usr/local/ssl/lib shared enable-ssl3 enable-ssl2 && \
    make all && make install_sw && rm -rf ../openssl-1.0.1f


#RUN curl http://www.dest-unreach.org/socat/download/socat-1.7.3.2.tar.gz -o socat.tar.gz
    #LIBS=-ldl LDFLAGS=-L/usr/local/ssl/lib CFLAGS=-I/usr/local/ssl/include ./configure --enable-openssl && \
COPY socat.tar.gz /socat.tar.gz
RUN tar xvf socat.tar.gz && \
    cd socat-1.7.3.2 && \
    LIBS=-ldl LDFLAGS="-L/usr/local/ssl/lib -Wl,-rpath=/usr/local/ssl/lib" CFLAGS=-I/usr/local/ssl/include ./configure --prefix=/usr --enable-openssl && \
    make && make install && rm -rf ../socat-1.7.3.2

#RUN curl https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz -o python.tar.gz
COPY python.tar.gz /python.tar.gz

COPY Setup.patch /Setup.patch

RUN tar xvf python.tar.gz && \
    cd Python-3.6.1 && \
    LIBS=-ldl LDFLAGS="-L/usr/local/ssl/lib -Wl,-rpath=/usr/local/ssl/lib" CFLAGS=-I/usr/local/ssl/include ./configure --prefix=/usr && \
    patch -p1 < /Setup.patch && \ 
    make all && make install && rm -rf ../Python-3.6.1

COPY curl.tar.gz /curl.tar.gz
RUN tar xvf curl.tar.gz && \
    cd curl-7.54.1 && \
    LDFLAGS="-Wl,-rpath=/usr/local/ssl/lib" ./configure --prefix=/usr --with-ssl=/usr/local/ssl && \
    make && make install && rm -rf ../curl-7.54.1

RUN mkdir /shared

VOLUME /shared
