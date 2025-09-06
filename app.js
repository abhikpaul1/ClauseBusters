const express = require('express');
const winston = require('winston');
const morgan = require('morgan');
const helmet = require('helmet');
const cors = require("cors");
const rateLimit = require("express-rate-limit");
const mongoSanitize = require("express-mongo-sanitize");
const xss = require("xss-clean");
const hpp = require("hpp");
const mongoose = require('mongoose');
const redis = require('redis');

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
    new winston.transports.Console({ format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )}),
    new winston.transports.File({ filename: 'app.log' })
  ],
});

// -------- Morgan HTTP Logger --------
app.use(morgan('combined', {
  stream: { write: (message) => logger.info(message.trim()) }
}));

// -------- Security Middleware --------
app.use(helmet());
app.use(cors({ origin: "*", methods: ["GET","POST","PUT","DELETE"] }));
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100, message: "Too many requests" }));
app.use(mongoSanitize());
app.use(xss());
app.use(hpp());
app.use(express.json());

// -------- Redis Setup --------
const redisClient = redis.createClient();
redisClient.connect().catch(err => logger.error('Redis connection error:', err));

// -------- MongoDB + Mongoose Setup --------
const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/mydb', {
      useNewUrlParser: true, useUnifiedTopology: true
    });
    console.log(`MongoDB connected: ${mongoose.connection.host}`); // :contentReference[oaicite:0]{index=0}
  } catch (err) {
    console.error('MongoDB connection failed:', err);
    process.exit(1);
  }
};
connectDB();

// Example Mongoose Model
const DocumentSchema = new mongoose.Schema({
  content: String,
  simplified: String,
}, { timestamps: true });
const Document = mongoose.model('Document', DocumentSchema);

// -------- Routes --------
app.get('/', (req, res) => {
  logger.info('Root route accessed');
  res.send('🚀 Hello Hackathon!');
});

// Status route with Redis caching
app.get('/status', async (req, res, next) => {
  const cacheKey = 'status';
  try {
    const cached = await redisClient.get(cacheKey);
    if (cached) return res.json(JSON.parse(cached));

    const response = { status: 'ok', time: new Date().toISOString() };
    await redisClient.set(cacheKey, JSON.stringify(response), { EX: 60 });
    return res.json(response);
  } catch (err) {
    return next(err);
  }
});

// Simplify legal document route with caching + MongoDB
app.post('/simplify', async (req, res, next) => {
  try {
    const { content } = req.body;
    if (!content) return res.status(400).json({ error: 'No content provided' });

    const hash = Buffer.from(content).toString('base64');
    const cacheKey = `doc:${hash}`;

    // Check cached simplified result
    const cached = await redisClient.get(cacheKey);
    if (cached) return res.json(JSON.parse(cached));

    // Check if stored in MongoDB
    let doc = await Document.findOne({ content }).lean().exec();
    if (doc) {
      await redisClient.set(cacheKey, JSON.stringify(doc), { EX: 300 });
      return res.json(doc);
    }

    // Otherwise, simplify with GenAI (mocked here)
    const simplified = `Simplified version of: ${content.substring(0, 50)}...`;

    // Store and cache new document
    doc = await Document.create({ content, simplified });
    await redisClient.set(cacheKey, JSON.stringify(doc), { EX: 300 });

    res.json(doc);
  } catch (err) {
    next(err);
  }
});

// Health route
app.get('/health', (req, res) => {
  logger.info('Health route accessed');
  res.json({ status: 'ok', uptime: process.uptime(), timestamp: new Date().toISOString() });
});

// Error-handling Middleware
app.use((err, req, res, next) => {
  logger.error(err.stack);
  res.status(500).send('Something broke!');
});

// Start Server
app.listen(PORT, () => {
  logger.info(`Server running on http://localhost:${PORT}`);
});

module.exports = app;
