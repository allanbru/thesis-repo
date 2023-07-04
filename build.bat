cd /D %~dp0
docker build -t thesis:initial . --build-arg DEBUG_DOMAIN=0
pause