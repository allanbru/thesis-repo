FROM python:3.9

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
    --no-install-recommends

# Download and install libu2f-udev
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/libu/libu2f-host/libu2f-udev_1.1.4-1_all.deb && \
    dpkg -i libu2f-udev_1.1.4-1_all.deb

# Download and install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb

# Download and install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P /tmp/ && \
    unzip -o /tmp/chromedriver_linux64.zip -d /tmp/ && \
    chmod +x /tmp/chromedriver && \
    mv /tmp/chromedriver /usr/local/bin/chromedriver

# Install Python dependencies without prompting for input
RUN python -m pip install --no-cache-dir --upgrade \
    requests \
    tldextract \
    python-whois \
    dnspython \
    selenium \
    ndjson \
    webdriver-manager

WORKDIR /app

# Set the user as root to perform administrative tasks
USER root

# Set up a non-root user
RUN useradd -u 1000 -g root -m -d /home/crawler -s /bin/bash crawler

# Create the desired directory and change its ownership and permissions
#RUN mkdir -p /app/screenshots \
#    && chown -R crawler:root /app/screenshots \
#    && chmod -R 777 /app/screenshots
#
#RUN mkdir -p /app/output \
#    && chown -R crawler:root /app/output \
#    && chmod -R 777 /app/output
#
#RUN chown -R crawler:root /app/* \
#    && chmod -R 777 /app/*

# Copy the Python script and input.csv to the working directory
COPY main.py .
COPY auxclock.py .
COPY browsermanager.py .
COPY domain.py .
#COPY input.csv .
#COPY log.log .

RUN chmod +x /app/*.py
#RUN chmod +w /app/log.log
#RUN chown -R 1000:root /app 

USER crawler

ARG DEBUG_DOMAIN=0

# Set the entrypoint command to run your main.py script
CMD python main.py --input /data/input.csv --output /data/output.csv --threads 1 --debug $DEBUG_DOMAIN

