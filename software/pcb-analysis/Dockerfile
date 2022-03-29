#***************************
# Build environment
#***************************
FROM python:3.8.11-slim-buster as build

# Copy the sources
COPY ./ .

# Setup the build environment
RUN pip install wheel

# Build the package
RUN python setup.py bdist_wheel && ls dist


#***************************
# Run environment
#***************************
FROM python:3.8.11-slim-buster

# Setup the working directory
RUN mkdir /opt/pcb-analysis
WORKDIR /opt/pcb-analysis

# Create the default instance folder
RUN mkdir /opt/pcb-analysis/instance

# Add a new non-root user "pcb-analysis" with user id 1337
RUN useradd -m -u 1337 pcb-analysis
RUN chown -R pcb-analysis:pcb-analysis .

# Change to non-root privilege
USER pcb-analysis
ENV PATH=$PATH:/home/pcb-analysis/.local/bin

# Copy the newly built package
COPY --from=build dist/*.whl .

# Install gunicorn as production server
RUN pip install gunicorn

# Install the package
RUN pip install $(ls -1 *.whl)

EXPOSE 5001
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "pcb_analysis.wsgi:app"]
