FROM python:3.6.10-buster

RUN apt-get update

# Copy conductor integration files
RUN pip install -i https://test.pypi.org/simple/ frinx-conductor-client

# Install package dependencies
RUN pip3 install requests

# Install dependencies of workers
COPY requirements.txt /home/app/requirements.txt
WORKDIR /home/app
RUN pip3 install -r requirements.txt

# Copy workers and workflows
COPY ./workers /home/app/workers
COPY ./workflows /home/app/workflows
COPY ./main.py /home/app

WORKDIR /home/app/
RUN python3 -m unittest workers/uniconfig_worker_test.py
RUN python3 -m unittest workers/netconf_worker_test.py
RUN python3 -m unittest workers/cli_worker_test.py
ENTRYPOINT [ "python3", "main.py" ]
