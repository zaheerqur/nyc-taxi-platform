FROM node:20-alpine
WORKDIR /app
COPY dashboard/package.json .
RUN npm install
COPY dashboard/vite.config.js .
CMD ["npm", "run", "dev"]
