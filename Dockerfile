FROM python:3.7-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt 
EXPOSE 5001
ENTRYPOINT [ "python" ] 
CMD [ "manage.py" ]