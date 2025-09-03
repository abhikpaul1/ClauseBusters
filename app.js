const express = require('express');
const winston = require('winston');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 4000;

// -------- Winston Logger Setup --------
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'app.log' })
  ],
});

// -------- Morgan HTTP Logger --------
app.use(morgan('combined', {
  stream: {
    write: (message) => logger.info(message.trim())
  }
}));

// -------- Routes --------
app.get('/', (req, res) => {
  logger.info('Root route accessed');
  res.send('🚀 Hello Hackathon!');
});

app.get('/status', (req, res) => {
  logger.info('Status route accessed');
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// 🔹 Health route (for uptime monitoring)
app.get('/health', (req, res) => {
  logger.info('Health route accessed');
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// -------- Start Server --------
app.listen(PORT, () => {
  logger.info(`Server running on http://localhost:${PORT}`);
});
