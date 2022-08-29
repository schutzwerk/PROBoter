#***************************
# Build environment
#***************************
FROM python:3.10.6-slim-buster as build

# Copy the sources
COPY ./ .

# Setup the build environment
RUN pip install wheel

# Build the package
RUN python setup.py bdist_wheel && ls dist


#***************************
# Run environment
#***************************
FROM python:3.10.6-slim-buster

# Setup the working directory
RUN mkdir /opt/signal-analysis
WORKDIR /opt/signal-analysis

# Create the default instance folder
RUN mkdir /opt/signal-analysis/instance

# Add a new non-root user "pcb-analysis" with user id 1338
RUN useradd -m -u 1338 signal-analysis
RUN chown -R signal-analysis:signal-analysis .

# Change to non-root privilege
USER signal-analysis
ENV PATH=$PATH:/home/signal-analysis/.local/bin

# Copy the newly built package
COPY --from=build dist/*.whl .

# Install gunicorn as production server
RUN pip install gunicorn

# Install the package
RUN pip install $(ls -1 *.whl)

EXPOSE 5002
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "signal_analysis.wsgi:app"]
