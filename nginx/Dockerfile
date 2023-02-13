FROM nginx:latest

# Update environment
RUN apt-get update && apt-get upgrade -y

# Add bash for boot cmd and vim
RUN apt-get install -y bash
RUN apt-get install -y vim

# manager certificate SSL
RUN apt-get install -y certbot python3-certbot-nginx cron

# Add nginx.config to container
COPY nginx.conf /etc/nginx/nginx.conf

# Add default.conf to container
COPY default.conf /etc/nginx/conf.d/default.conf

# abilito il rinnovo automatico del certificato
RUN echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

