FROM python:3.10.5-alpine3.16

RUN apk add make jpeg-dev zlib-dev alpine-sdk

WORKDIR /app
COPY . /app

RUN make install

ENTRYPOINT [ "make" ] 
CMD [ "run" ]
