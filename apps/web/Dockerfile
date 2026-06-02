# Test Commander web console - Next.js frontend (Phase 10).
FROM node:22-slim

WORKDIR /srv

COPY apps/web/package.json ./package.json
RUN npm install

COPY apps/web ./

ENV TC_API_BASE=http://api:8100
EXPOSE 3100

CMD ["npm", "run", "dev"]
