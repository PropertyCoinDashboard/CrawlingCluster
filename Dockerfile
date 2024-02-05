FROM apache/airflow:2.6.2

# Switch to the Airflow user
USER root

# Copy requirements.txt
COPY requirements.txt ./requirements.txt

# Install Python dependencies as the airflow user
RUN apt-get update && apt-get install -y libgeos-dev && apt-get autoremove -yqq --purge && apt-get clean

USER airflow
RUN pip install -r ./requirements.txt