FROM nginx:alpine

# Install Python and inotify-tools
RUN apk add --no-cache \
    python3 \
    inotify-tools \
    bash

# Create app directory
RUN mkdir -p /app

# Copy scripts
COPY generator.py /app/
COPY watcher.sh /app/
COPY nginx.conf /etc/nginx/nginx.conf

# Make scripts executable
RUN chmod +x /app/watcher.sh /app/generator.py

# Create html directory with proper permissions
RUN mkdir -p /var/www/html && \
    chown -R nginx:nginx /var/www/html

# Expose port
EXPOSE 80

# Create entrypoint script with proper permissions.
# /var/www/html is deliberately left alone: it is usually a bind mount from the
# host, where a recursive chown would take the user's own content directory away
# from them. generator.py gives each index.html the ownership of its directory
# instead. nginx is exec'd so that it is PID 1 and receives SIGTERM on stop.
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo '/app/watcher.sh &' >> /entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
