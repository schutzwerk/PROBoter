#***************************
# Build environment
#***************************
FROM node:16.4-alpine AS build

RUN mkdir /opt/web-ui
WORKDIR /opt/web-ui

# Copy the sources
COPY ./ .

# Setup the build environment
RUN npm install

# Build for production
RUN npm run build


#***************************
# Run environment
#***************************
FROM nginx:1.21-alpine
COPY --from=build /opt/web-ui/dist/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
