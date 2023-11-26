# Phishing Crawler

# Introduction
This project is a web crawler that aims to stop phishing. In order to do so, it gets several information about websites' SSL certificates, DNS and WHOIS records.

The output consists of one ndjson file and one 

# Installation

I suggest using Docker's version, however, if you would use it from source, here are the steps toward using the Crawler:


# Docker

You can run this project in Docker using the following command:

```cmd
    docker run --name phishingcrawler ^
		-p 9018:9018 ^
		--env-file .env ^
		-v /path/to/output/:/app/output ^
		-v /path/to/screenshots/:/app/screenshots ^
		allanbru/thesis:latest
```

## Parameters

### Port
By default, system uses the 9018 port for communication purposes with the .NET core Screenshoter. You can change the exposed port in the .env file, but make sure to **change it in the command line as well!**.
