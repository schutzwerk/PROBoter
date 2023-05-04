#***************************
# Run environment
#***************************
FROM python:3.10.6-buster

# Install dependencies
RUN apt-get update && apt-get install -y \
    udev \
    curl

# Setup the working directory
RUN mkdir /opt/hardware-control
WORKDIR /opt/hardware-control

# Create the default instance folder
RUN mkdir /opt/hardware-control/instance

# Copy the newly built package and other dependencies
COPY ./ .

# Install the package
RUN pip install ./libs/mtracker-0.0.1-py3-none-any.whl
RUN pip install -e ./

# Set environment variables to configure quart
ENV QUART_APP=proboter
ENV QUART_HARDWARE_BACKEND=simulation

CMD ["quart", "run", "-h", "0.0.0.0", "-p", "5003"]
