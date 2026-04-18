FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --production --quiet

COPY . .

RUN mkdir -p /app/uploads /app/data

ENV NODE_ENV=production \
    PORT=4444 \
    DATA_DIR=/app/data \
    UPLOADS_DIR=/app/uploads

EXPOSE 4444

CMD ["node", "server.js"]