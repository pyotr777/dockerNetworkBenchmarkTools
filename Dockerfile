FROM peter/iperf
MAINTAINER Bryzgalov Peter @ AICS RIKEN
ADD client_startup.sh /client_startup.sh
ADD getiperfresults.py /getiperfresults.py
RUN chmod +x /client_startup.sh
EXPOSE 22 5001
ENTRYPOINT ["/client_startup.sh"]
