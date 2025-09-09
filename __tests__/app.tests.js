const request = require('supertest');
const mongoose = require('mongoose');

// Mock Redis to prevent connection errors
jest.mock('redis', () => {
  return {
    createClient: jest.fn(() => ({
      connect: jest.fn(),
      get: jest.fn().mockResolvedValue(null),
      set: jest.fn().mockResolvedValue('OK'),
      on: jest.fn(),
      isOpen: true
    }))
  };
});

const app = require('../app');

// ... (your existing code)

// Mock Mongoose Document model
jest.mock('mongoose', () => {
  const actualMongoose = jest.requireActual('mongoose');
  const mockDocument = {
    // Mock the findOne method and its chained methods
    findOne: jest.fn(() => ({
      lean: jest.fn(() => ({
        exec: jest.fn().mockResolvedValue(null)
      }))
    })),
    create: jest.fn(),
  };

  return {
    ...actualMongoose,
    connect: jest.fn().mockResolvedValue(),
    model: jest.fn(() => mockDocument),
    __esModule: true,
  };
});

// ... (your existing describe block)

it('POST /simplify should simplify and store a valid document', async () => {
    // Mock the Mongoose create method to return a dummy object
    require('mongoose').model('Document').create.mockResolvedValue({
        content: 'Test content',
        simplified: 'Mocked simplified text',
    });

    const response = await request(app)
        .post('/simplify')
        .send({ content: 'Test content' });
    
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('simplified', 'Mocked simplified text');
});

describe('App Basic Functionality', () => {
  it('should start without errors', () => {
    expect(app).toBeDefined();
  });

  it('GET / should return hello message', async () => {
    const response = await request(app).get('/');
    expect(response.status).toBe(200);
    expect(response.text).toContain('Hello Hackathon');
  });

  it('GET /health should return health status', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ok');
  });

  it('POST /simplify should validate input', async () => {
    const response = await request(app)
      .post('/simplify')
      .send({});
    expect(response.status).toBe(400);
    expect(response.body.error).toBe('No content provided');
  });
});

