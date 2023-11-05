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
RUN wget -N https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip -P /tmp/ && \
    unzip -o /tmp/chromedriver-linux64.zip -d /tmp/ && \
    chmod +x /tmp/chromedriver-linux64/chromedriver && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver

# Install Python dependencies without prompting for input
RUN python -m pip install --no-cache-dir --upgrade \
    requests \
    tldextract \
    python-whois \
    dnspython \
    selenium \
    ndjson \
    webdriver-manager

# Download and install dotnet SDK
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-7.0

WORKDIR /app

# Download and install Screenshoter
RUN wget -N https://www.site.allanbr.net/screenshoter.zip -P /tmp/ && \
    unzip -o /tmp/screenshoter.zip -d /app/ && \
    chmod +x /app/screenshoter/PhishingCrawler && \
    chmod +x /app/screenshoter/selenium-manager/linux/selenium-manager

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
COPY browsermanager.py .
COPY domain.py .
COPY input.csv .
COPY log.log .

RUN chmod +x /app/*.py
RUN chmod +w /app/log.log
RUN chown -R 1000:root /app 

USER crawler

ARG DEBUG_DOMAIN=0
ARG THREADS=1
ARG INPUT=input.csv
ARG OUTPUT=output.csv
ARG SCREENSHOT_ONLY=0
ARG NS1=8.8.8.8
ARG NS2=4.4.4.4

# Set the entrypoint command to run your main.py script
CMD python main.py --input $INPUT --output $OUTPUT --threads $THREADS --debug $DEBUG_DOMAIN --screenshot_only $SCREENSHOT_ONLY --ns1 $NS1 --ns2 $NS2