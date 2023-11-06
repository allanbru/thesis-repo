#!/bin/bash 

docker run -v $(pwd)/data:/data -it --user $UID  phishingcrawler /bin/bash
