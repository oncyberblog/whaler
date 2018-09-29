FROM nginx
RUN apt-get update && apt-get install -y curl
RUN rm /etc/nginx/conf.d/default.conf

COPY content /usr/share/nginx/html

COPY conf /

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD /run.sh
