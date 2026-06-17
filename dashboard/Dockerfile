FROM node:20-alpine AS build
WORKDIR /app
COPY dashboard/package.json .
RUN npm install
COPY dashboard/vite.config.js .
COPY dashboard/index.html .
COPY dashboard/src/ src/
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
