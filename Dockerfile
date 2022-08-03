FROM elixir:1.12
WORKDIR /gradualelixir
COPY requirements.txt /gradualelixir/
COPY src /gradualelixir/src

RUN mix do local.hex --force
COPY ./elixir_port /gradualelixir/elixir_port/
COPY ./elixir_port/mix.exs ./elixir_port/mix.lock /gradualelixir/elixir_port/
WORKDIR /gradualelixir/elixir_port/
RUN mix deps.get --only $MIX_ENV
RUN mix deps.compile
COPY ./elixir_port/lib lib
RUN mix compile

RUN apt-get update && apt-get install -y software-properties-common gcc
RUN apt-get update && apt-get install -y python3.6 python3-distutils python3-pip python3-apt
RUN pip install -r /gradualelixir/requirements.txt
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH "${PYTHONPATH}:/gradualelixir/src/"

ENV DOCKER=true
RUN touch /gradualelixir/.env
RUN echo "PROJECT_PATH=/gradualelixir/" >> /gradualelixir/.env
RUN echo "ELIXIR_PATH=$(which elixir)" >> /gradualelixir/.env
RUN echo "WORKING_DIR=/resources" >> /gradualelixir/.env

WORKDIR /resources/
WORKDIR /

RUN touch /bin/gradualelixir
RUN echo '#!/bin/bash' >> /bin/gradualelixir
RUN echo 'python3 /gradualelixir/src/gradualelixir/cli.py "$@"' >> /bin/gradualelixir
RUN chmod +x '/bin/gradualelixir'

ENTRYPOINT ["gradualelixir"]
