FROM node:22-alpine

WORKDIR /app
COPY apps/web/package*.json /app/
RUN npm ci
COPY apps/web /app

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
