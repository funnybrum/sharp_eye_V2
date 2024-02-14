FROM ubuntu:22.04
MAINTAINER funnybrum@gmial.com

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get -y install apt-utils cron python3 python3-pip python3-opencv ffmpeg tzdata curl nano wget
RUN apt-get -y install libmfx1 libmfx-tools libva-drm2 libva-x11-2 vainfo intel-media-va-driver-non-free ocl-icd-libopencl1
RUN apt-get -y install --only-upgrade libigdgmm12

RUN wget -q -O /tmp/tmp.deb https://github.com/intel/compute-runtime/releases/download/23.52.28202.14/libigdgmm12_22.3.11_amd64.deb \
  && dpkg -i /tmp/tmp.deb \
  && rm /tmp/tmp.deb

RUN wget -q -O /tmp/tmp.deb https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.15770.11/intel-igc-core_1.0.15770.11_amd64.deb \
  && dpkg -i /tmp/tmp.deb \
  && rm /tmp/tmp.deb

RUN wget -q -O /tmp/tmp.deb https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.15770.11/intel-igc-opencl_1.0.15770.11_amd64.deb \
  && dpkg -i /tmp/tmp.deb \
  && rm /tmp/tmp.deb

RUN wget -q -O /tmp/tmp.deb https://github.com/intel/compute-runtime/releases/download/23.52.28202.14/intel-level-zero-gpu_1.3.28202.14_amd64.deb \
  && dpkg -i /tmp/tmp.deb \
  && rm /tmp/tmp.deb

RUN wget -q -O /tmp/tmp.deb https://github.com/intel/compute-runtime/releases/download/23.52.28202.14/intel-opencl-icd_23.52.28202.14_amd64.deb \
  && dpkg -i /tmp/tmp.deb \
  && rm /tmp/tmp.deb

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
