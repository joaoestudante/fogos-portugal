# Build step #1: build the React front end
FROM node:20-alpine as build-step
WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY package.json ./
COPY . .
RUN npm install --legacy-peer-deps
RUN npm run build

# Build step #2: build an nginx container
FROM nginx:stable-alpine
COPY --from=build-step /app/dist /usr/share/nginx/html
COPY ./nginx.conf /etc/nginx/conf.d/default.conf