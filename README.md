
# Phishing Crawler

# Introduction
This project is a web crawler that aims to stop phishing. In order to do so, it gets several information about websites' SSL certificates, DNS and WHOIS records.

The output consists of one ndjson file with all the collected information and one folder with screenshots for every domain.

**NOTE**: due to performance reasons, all "screenshot_file_path" variables are coming out null on the ndjson. This should be fixed in the future.

# Installation

I suggest using Docker's version, however, if you would rather run it from source, here are the steps toward using the Crawler in a Linux machine:

```bash
git clone https://github.com/allanbru/thesis-repo.git
cd thesis-repo
pip install -r requirements.txt
mkdir output && chmod 777 output
mkdir screenshots && chmod 777 screenshots
chmod +x ./Screenshoter
chmod +x ./selenium-manager/linux/selenium-manager
/usr/bin/bash start.sh $LOCALHOST $LOCALPORT $THREADS $NS1 $NS2 $DEBUG_DOMAIN
```
See [parameters](#Parameters) for more info

# Docker

You can run this project in Docker using the following command:

```bash
docker run --name phishingcrawler ^
			-p 9018:9018 ^
			--env-file .env ^
			-v /path/to/output/:/app/output ^
			-v /path/to/screenshots/:/app/screenshots ^
			allanbru/thesis:latest
```
Include a valid local volume path to save the obtained results.
It is also advised to have a .env file containing information about the running environment. Example:
```js
DEBUG_DOMAIN=0
THREADS=4
NS1=8.8.8.8
NS2=4.4.4.4
LOCALHOST=127.0.0.1
LOCALPORT=9018
```
## Parameters

### DEBUG DOMAIN
From input.csv, select a domain to analyze its homophones ONLY. Then, enter its id as in the environment variable. If DEBUG_DOMAIN=0, then all domains are going to be analyzed. 

### THREADS
The number of threads in which the python script and the Screenshoter will run.

### NS
Nameservers for getting DNS data: default is NS1=8.8.8.8 and NS2=4.4.4.4

### LOCALHOST
By default, 127.0.0.1. Change it only if you want to expose the screenshoter to external calls or if you have another address for localhost.

### LOCALPORT
By default, system uses the 9018 port for communication purposes with the .NET core Screenshoter. You can change the exposed port in the .env file, but make sure to **change it in the command line as well!**.
