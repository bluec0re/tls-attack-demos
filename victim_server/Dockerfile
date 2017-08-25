FROM ssl-demos

RUN echo "[*] Creating certificate" && /usr/local/ssl/bin/openssl req -new -out cert.req -subj '/CN=*.goodbank.com' -days 2048 -passout pass:foobar && \
    echo "[*] Decrypting privatekey" && /usr/local/ssl/bin/openssl rsa -in privkey.pem -out privkey2.pem -passin pass:foobar && \
    mv privkey2.pem privkey.pem && \
    echo "[*] Signing cert" && /usr/local/ssl/bin/openssl x509 -req -in cert.req -out cert.pem -signkey privkey.pem


COPY start_socats.py /start_socats.py

ENTRYPOINT ["python3", "/start_socats.py"]
