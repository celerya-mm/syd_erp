# Start with Debian Python 3.11 base image

FROM python:3.11-bullseye

MAINTAINER Marco Mazzini <mazzini@celerya.com>

RUN pip install --upgrade pip
RUN pip install pipenv

# Update environment
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get clean && apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc

# Show stdout and stderr outputs instantly without buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# get library
RUN apt-get install -y apt-utils
RUN apt-get install -y dialog
RUN apt-get install -y wkhtmltopdf

# get curl for healthchecks and vim for write config file
RUN apt-get install -y curl
RUN apt-get install -y vim

# Directory app
RUN mkdir -p /home/app/src
RUN mkdir -p /var/log/app && \
    touch /var/log/app/flask-app.err.log && \
    touch /var/log/app/flask-app.out.log

# Copy from "host" to "container"
COPY . /home/app/src

# venv
ENV VIRTUAL_ENV=/home/app/venv

# python setup
RUN python3.11 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# add user
RUN useradd -ms /bin/bash celerya
WORKDIR /home/app

# Install dependencies
RUN $VIRTUAL_ENV/bin/python3.11 -m pip install -U --no-cache-dir pip setuptools wheel
RUN grep -v "pywin32" /home/app/src/requirements.txt | xargs $VIRTUAL_ENV/bin/python3.11 -m pip --no-cache-dir install --use-pep517

# clean package manager cache to reduce your custom image size...
RUN apt-get clean all \
    && rm -rvf /var/lib/apt/lists/*

# Add all files from current directory on host to dockerised directory in container
COPY . .

# set entrypoint for run with gunicorn in production
ENTRYPOINT ["./gunicorn.sh"]

# set entrypoint for run in develop mode
#ENTRYPOINT ["python3"]
#CMD ["-m", "flask", "run"]
