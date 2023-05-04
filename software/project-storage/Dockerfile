#***************************
# Build environment
#***************************
FROM python:3.10.6-slim-bullseye as build
COPY ./ .
RUN pip install wheel
RUN python setup.py bdist_wheel && ls dist


#***************************
# Run environment
#***************************
FROM python:3.10.6-slim-bullseye

# Install dependencies
RUN apt-get update && apt-get install -y \
    libglfw3 \
    curl

# Setup the working directory
RUN mkdir /opt/project_storage
WORKDIR /opt/project_storage


# Add a new non-root user "project_storage" with user id 1339
RUN useradd -m -u 1339 project-storage
RUN chown -R project-storage:project-storage .
ENV PATH=${PATH}:/home/project-storage/.local/bin

# Create the default dat folder
RUN mkdir -p /var/project-storage/instance
RUN chown project-storage:project-storage /var/project-storage

# Copy the newly built package
COPY --from=build dist/*.whl .

# Install gunicorn as production server
RUN pip install gunicorn

# Install the package
RUN pip install $(ls -1 *.whl)

# Change to non-root privilege
# IMPORTANT: Prior installation steps have
#            are executed as 'root' so that
#            the application software is
#            available to all users which
#            is intended here (see Makefile)
USER project-storage

# Default settings
env FLASK_INSTANCE_PATH=/var/project-storage/instance
env FLASK_SQLALCHEMY_DATABASE_URI=sqlite:////var/project-storage/pcb_data.sqlite

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "project_storage.wsgi:app"]
