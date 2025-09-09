describe('Application Landing Page', () => {
  it('should visit the home page', () => {
    cy.visit('http://localhost:4000'); // Visit your local server's URL
    cy.contains('Hello Hackathon!'); // Assert that the page contains this text
  });
});