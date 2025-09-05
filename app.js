const express = require('express');
const winston = require('winston');
const morgan = require('morgan');
const helmet = require('helmet');
const cors = require("cors");
const rateLimit = require("express-rate-limit");
const mongoSanitize = require("express-mongo-sanitize");
const xss = require("xss-clean");
const hpp = require("hpp");

const app = express();
const PORT = process.env.PORT || 4000;

// -------- Winston Logger Setup --------
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    new winston.transports.File({ filename: 'app.log' })
  ],
});

// -------- Morgan HTTP Logger --------
app.use(morgan('combined', {
  stream: {
    write: (message) => logger.info(message.trim())
  }
}));

// -------- Security Middleware --------
app.use(helmet());
app.use(cors({
  origin: "*", // change to your frontend domain in production
  methods: ["GET", "POST", "PUT", "DELETE"] // Enclosed methods in an array
}));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP
  message: "Too many requests, please try again later."
});
app.use(limiter);

app.use(mongoSanitize());
app.use(xss());
app.use(hpp());

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

// -------- Error Handling Middleware --------
app.use((err, req, res, next) => {
  logger.error(err.stack);
  res.status(500).send('Something broke!');
});

// -------- Start Server --------
app.listen(PORT, () => {
  logger.info(`Server running on http://localhost:${PORT}`);
});

module.exports = app;