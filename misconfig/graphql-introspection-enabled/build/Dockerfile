# A stock Apollo GraphQL server. Introspection is a server setting
# (INTROSPECTION env, per state): on exposes the full schema to anyone; off
# (the production default) refuses __schema queries. Apollo's built-in health
# endpoint stays up either way.
FROM node:18-slim
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY index.js .
EXPOSE 4000
CMD ["node", "index.js"]
