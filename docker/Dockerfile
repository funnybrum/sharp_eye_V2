FROM ubuntu:24.04
LABEL maintainer="funnybrum@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y install \
    apt-utils cron python3 python3-pip python3-opencv ffmpeg tzdata curl nano wget \
    libvpl2 libmfx-gen1.2 libva-drm2 libva-x11-2 vainfo intel-media-va-driver-non-free \
    ocl-icd-libopencl1 intel-opencl-icd \
  && rm -rf /var/lib/apt/lists/*

# Cron setup
ADD docker/crontab /etc/cron.d/schedule
RUN chmod 0644 /etc/cron.d/schedule
RUN crontab /etc/cron.d/schedule
RUN touch /var/log/cron.log

# Python scripts
ADD requirements.txt /
RUN pip3 install --break-system-packages -r requirements.txt
ADD src/main /sharp_eye

# Set the correct timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Sofia /etc/localtime && echo Europe/Sofia > /etc/timezone

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log

EXPOSE 8080
