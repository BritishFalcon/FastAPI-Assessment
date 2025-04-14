FROM node:20-bookworm

# Set working dir
WORKDIR /app_new

# Install pnpm globally
RUN npm install -g pnpm

# Copy only the lockfiles + package.json first
COPY package.json pnpm-lock.yaml* ./

# Install deps before copying source
RUN pnpm install

# Copy the rest of the source code
COPY . .

# Make sure node has permission (optional, if you use USER node)
# RUN chown -R node:node /app
# USER node

EXPOSE 3000

CMD ["pnpm", "dev"]
