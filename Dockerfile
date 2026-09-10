# --- Stage 1 : build de l'application Vue ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.mjs authService.js passwordsService.js vaultCrypto.js ./
COPY src/ src/

# On ne copie volontairement pas le .env : en production, l'app doit appeler
# l'API en chemin relatif (/api/...) puisque nginx fait office de reverse proxy
# vers le service "backend" (voir authService.js / passwordsService.js).
RUN npm run build

# --- Stage 2 : service des fichiers statiques + reverse proxy HTTPS ---
FROM nginx:1.27-alpine

RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/certs \
    && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout /etc/nginx/certs/selfsigned.key \
       -out /etc/nginx/certs/selfsigned.crt \
       -subj "/CN=localhost"

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443
