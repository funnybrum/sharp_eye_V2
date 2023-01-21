FROM ubuntu:20.04
MAINTAINER funnybrum@gmial.com

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get -y install cron && \
    apt-get -y install python3 python3-pip && \
    apt-get -y install python3-opencv && \
    apt-get -y install ffmpeg && \
    apt-get -y install tzdata && \
    apt-get -y install curl && \
    apt-get -y install nano

# Cron setup
ADD docker/crontab /etc/cron.d/schedule
RUN chmod 0644 /etc/cron.d/schedule
RUN crontab /etc/cron.d/schedule
RUN touch /var/log/cron.log

# Python scripts
ADD requirements.txt /
RUN pip3 install -r requirements.txt
ADD src/main /sharp_eye

# Set the correct timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Sofia /etc/localtime && echo Europe/Sofia > /etc/timezone

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log

EXPOSE 8080