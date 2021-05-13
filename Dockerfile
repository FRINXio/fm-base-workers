FROM python:3.6.10-buster

RUN apt-get update

# Install dependencies of workers
COPY requirements.txt /home/app/requirements.txt
WORKDIR /home/app
RUN pip3 install -r requirements.txt

# Copy workers and workflows
COPY ./frinx_conductor_workers /home/app/frinx_conductor_workers
COPY ./workflows /home/app/workflows
COPY ./main.py /home/app

WORKDIR /home/app/
RUN python3 -m unittest frinx_conductor_workers/uniconfig_worker_test.py
RUN python3 -m unittest frinx_conductor_workers/netconf_worker_test.py
RUN python3 -m unittest frinx_conductor_workers/cli_worker_test.py
ENTRYPOINT [ "python3", "main.py" ]
