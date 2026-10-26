# A stock Node.js app. Safe by default; the vulnerable state starts it with
# --inspect bound to 0.0.0.0, exposing the V8 inspector debugger (an RCE
# surface) on :9229. The app itself is identical in both states.
FROM node:18-slim
WORKDIR /app
COPY server.js .
EXPOSE 3000 9229
CMD ["node", "server.js"]
