FROM python:3.12.1
# Copy Files
WORKDIR /usr/src/app
COPY airpollution/backend/backend.py airpollution/backend/backend.py
COPY airpollution/frontend airpollution/frontend/
# Install
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
# Docker Run Command
EXPOSE 5000
ENV FLASK_APP=/usr/src/app/airpollution/backend/backend.py
CMD [ "python", "-m" , "flask" , "run", "--host=0.0.0.0"]