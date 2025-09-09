// __tests__/simplify.integration.test.js

const request = require('supertest');
const app = require('../app');
const mongoose = require('mongoose');
const redis = require('redis');

describe('Simplify Route Integration Tests', () => {
    let server;
    let redisClient;

    beforeAll(async () => {
        // Manually connect to the databases from within the test
        const mongoUri = 'mongodb://127.0.0.1:27017/testdb';
        await mongoose.connect(mongoUri);

        // Redis client setup for tests
        redisClient = redis.createClient({ url: 'redis://127.0.0.1:6379' });
        await redisClient.connect();

        // Start the server on a different port
        server = app.listen(4001);
        // This is crucial: make your test wait for the server to be ready
        await new Promise(resolve => setTimeout(resolve, 500)); 
    });

    afterAll(async () => {
        // Clean up resources after the test
        await mongoose.connection.close();
        await redisClient.quit();
        await new Promise(resolve => server.close(resolve));
    });

    // Your test case
    it('should create a new simplified document in MongoDB', async () => {
        // ... (Your existing test code here)
    });
});

