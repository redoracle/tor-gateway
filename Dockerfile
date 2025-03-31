FROM alpine:latest

# Install required system packages and build dependencies
RUN apk --no-cache add \
    privoxy \
    tor \
    runit \
    python3 \
    py3-pip \
    curl \
    jq \
    build-base \
    python3-dev \
    libffi-dev

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    flask \
    requests \
    psutil \
    stem

# Expose Privoxy default port (and the web UI port 5000)
EXPOSE 8118 5000

# Define environment variables if needed (example)
ENV TOR_CONFIG_PATH=/etc/tor/torrc

# Create a non-root user and group for enhanced security
RUN addgroup -S dockerusers && \
    adduser -S -G dockerusers dockeruser

# Allow dockeruser to modify Tor configuration
RUN chown -R dockeruser:dockerusers /etc/tor

# Copy service configurations and our web UI code
COPY service/ /etc/service/
COPY torvariables.sh /home/dockeruser/
COPY app.py /home/dockeruser/
COPY templates/ /home/dockeruser/templates/
COPY static/ /home/dockeruser/static/
COPY .env /home/dockeruser/.env

# Ensure correct permissions for non-root execution
RUN chown -R dockeruser:dockerusers /etc/service /home/dockeruser && \
    chmod +x /home/dockeruser/torvariables.sh

RUN mkdir -p /var/lib/tor && \
chown -R dockeruser:dockerusers /var/lib/tor

# Set work directory
WORKDIR /home/dockeruser

# Switch to non-root user
USER dockeruser

# Define health check for better container monitoring
HEALTHCHECK --interval=60s --timeout=5s CMD nc -z localhost 8118 || exit 1

# Entrypoint: run torvariables.sh then start runit which will run all services (tor, privoxy, and webui)
ENTRYPOINT ["/home/dockeruser/torvariables.sh"]
CMD ["runsvdir", "/etc/service"]