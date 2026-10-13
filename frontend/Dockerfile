FROM node:24-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

RUN npm install -g @angular/cli@21

COPY . .

EXPOSE 4200

CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]