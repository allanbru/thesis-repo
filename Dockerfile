FROM ubuntu:latest

# Install necessary system dependencies without confirmation
RUN apt-get update && \
    apt-get install -y \
    wget \
    curl \
    unzip \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libvulkan1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    python3-pip \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    --no-install-recommends

# Download and install libu2f-udev
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/libu/libu2f-host/libu2f-udev_1.1.4-1_all.deb && \
    dpkg -i libu2f-udev_1.1.4-1_all.deb

# Download and install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb

# Download and install ChromeDriver
RUN wget -N https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip -P /tmp/ && \
    unzip -o /tmp/chromedriver-linux64.zip -d /tmp/ && \
    chmod +x /tmp/chromedriver-linux64/chromedriver && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver

WORKDIR /app

# Set the user as root to perform administrative tasks
USER root

# Set up a non-root user
RUN useradd -u 1000 -g root -m -d /home/crawler -s /bin/bash crawler

# Create the desired directory and change its ownership and permissions
RUN mkdir -p /app/screenshots \
    && chown -R crawler:root /app/screenshots \
    && chmod -R 777 /app/screenshots

RUN mkdir -p /app/output \
    && chown -R crawler:root /app/output \
    && chmod -R 777 /app/output

RUN chown -R crawler:root /app/* \
    && chmod -R 777 /app/*

# Copy the Python script and input.csv to the working directory
COPY main.py .
COPY auxclock.py .
COPY domain.py .
COPY input.csv .
COPY log.log .
COPY requirements.txt .
COPY capture_socket.py .
COPY Screenshoter .
COPY Screenshoter.pdb .
COPY selenium-manager selenium-manager
COPY selenium-manager/linux selenium-manager/linux
COPY selenium-manager/linux/selenium-manager selenium-manager/linux/selenium-manager
COPY start.sh .

RUN chmod +x /app/*.py
RUN chmod +x /app/Screenshoter
RUN chmod +x /app/selenium-manager/linux/selenium-manager
RUN chmod +x /app/start.sh
RUN chmod +w /app/log.log
RUN chown -R 1000:root /app 

USER crawler

ENV DEBUG_DOMAIN=0
ENV THREADS=4
ENV NS1=8.8.8.8
ENV NS2=4.4.4.4
ENV LOCALHOST=127.0.0.1
ENV LOCALPORT=9018

EXPOSE ${LOCALPORT}

RUN python3 -m pip install -r requirements.txt --no-cache-dir --upgrade

# Expose volumes for screenshots and output
VOLUME ["/app/screenshots", "/app/output"]

# Set the entrypoint command to run your main.py script
CMD sh start.sh $LOCALHOST $LOCALPORT $THREADS $NS1 $NS2 $DEBUG_DOMAIN