FROM node:22-alpine

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the project
COPY . .

# Vite development server
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]