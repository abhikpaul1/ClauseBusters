# Use Node.js 18
FROM node:18

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy rest of the app
COPY . .

# Expose port
EXPOSE 4000

# Start the app
CMD ["node", "app.js"]
