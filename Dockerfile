# Single stage for runtime
FROM node:20-alpine
WORKDIR /app

# Create a non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S clausebuster -u 1001

# 1. COPY DEPENDENCY FILES FIRST - This allows caching of npm install
COPY package*.json ./
# 2. INSTALL DEPS - This step is cached if package*.json doesn't change
RUN npm ci --only=production

# 3. COPY EVERYTHING ELSE - This happens after the cached npm install
COPY --chown=clausebuster:nodejs . .

# Switch to the non-root user
USER clausebuster

EXPOSE 4000
CMD ["node", "app.js"]