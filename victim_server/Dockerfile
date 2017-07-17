FROM debian

RUN apt-get update && apt-get install -y curl build-essential zlib1g-dev screen \
    && rm -rf /var/lib/apt/lists/*

# last heartbleed version
RUN curl https://www.openssl.org/source/old/1.0.1/openssl-1.0.1f.tar.gz -o openssl.tar.gz
RUN tar xvf openssl.tar.gz && \
    cd openssl-1.0.1f && \
    ./Configure linux-x86_64 && \
    make all
RUN cd openssl-1.0.1f && make install_sw && rm -rf ../openssl-1.0.1f


RUN curl http://www.dest-unreach.org/socat/download/socat-1.7.3.2.tar.gz -o socat.tar.gz
RUN tar xvf socat.tar.gz && \
    cd socat-1.7.3.2 && \
    LIBS=-ldl LDFLAGS=-L/usr/local/ssl/lib CFLAGS=-I/usr/local/ssl/include ./configure --enable-openssl && \
    make install && rm -rf ../socat-1.7.3.2

RUN curl https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz -o python.tar.gz
RUN tar xvf python.tar.gz && \
    cd Python-3.6.1 && \
    LIBS=-ldl LDFLAGS=-L/usr/local/ssl/lib CFLAGS=-I/usr/local/ssl/include ./configure && \
    make all && make install && rm -rf ../Python-3.6.1

RUN echo "[*] Creating certificate" && openssl req -new -out cert.req -subj '/CN=*.goodbank.com' -days 2048 -passout pass:foobar && \
    echo "[*] Decrypting privatekey" && openssl rsa -in privkey.pem -out privkey2.pem -passin pass:foobar && \
    mv privkey2.pem privkey.pem && \
    echo "[*] Signing cert" && openssl x509 -req -in cert.req -out cert.pem -signkey privkey.pem

RUN mkdir /shared

COPY start_socats.py /start_socats.py

VOLUME /shared

ENTRYPOINT ["python3", "/start_socats.py"]
