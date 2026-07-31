FROM busybox:latest
COPY script/app.sh /app.sh
RUN sed -i 's/\r$//' /app.sh && chmod +x /app.sh
EXPOSE 18080
CMD ["/app.sh"]
