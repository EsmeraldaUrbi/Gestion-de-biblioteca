FROM node:24-alpine
WORKDIR /app
RUN npm install -g @angular/cli@21
EXPOSE 4200
# El comando inicial se sobreescribirá temporalmente al crear el proyecto
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]