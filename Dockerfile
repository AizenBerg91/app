FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --production

COPY . .

RUN mkdir -p uploads videos data

EXPOSE 4444

CMD ["node", "server.js"]