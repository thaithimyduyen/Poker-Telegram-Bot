FROM python:3.10.5-alpine3.16

RUN apk add make jpeg-dev zlib-dev alpine-sdk

COPY requirements.txt makefile ./
RUN make install

WORKDIR /app
COPY . /app

ENTRYPOINT [ "make" ] 
CMD [ "run" ]
