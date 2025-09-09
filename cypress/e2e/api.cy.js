describe('API Endpoints', () => {
  it('should test the health endpoint', () => {
    cy.request('GET', 'http://localhost:4000/health').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('status', 'ok');
    });
  });

  it('should test the simplify endpoint', () => {
    const payload = { content: 'This is a complex legal document to be simplified.' };
    cy.request('POST', 'http://localhost:4000/simplify', payload).then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('simplified').to.be.a('string');
    });
  });
});