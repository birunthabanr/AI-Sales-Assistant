import React from "react";
import { MemoryRouter } from "react-router-dom";
import { mount } from "cypress/react";
import Chat from "../../src/pages/Chat";

describe("<Chat />", () => {
  beforeEach(() => {
    // Mock backend response
    cy.intercept("POST", "http://localhost:5000/chat", {
      statusCode: 200,
      body: { action: "chat", result: "Hello from bot!" },
    }).as("chatApi");

    // Mount component
    mount(
      <MemoryRouter>
        <Chat />
      </MemoryRouter>
    );
  });

  it("renders AI Assistant header", () => {
    cy.contains("AI Assistant").should("be.visible");
  });

  it("shows empty state message on first load", () => {
    cy.contains("Start a conversation").should("be.visible");
  });

  it("allows typing in input", () => {
    cy.get("input[placeholder='Type your message...']")
      .type("Hello there")
      .should("have.value", "Hello there");
  });

  it("sends a message and shows user bubble", () => {
    cy.get("input[placeholder='Type your message...']").type("Hi{enter}");
    cy.contains("Hi").should("be.visible");
  });

  it("shows loading animation after sending", () => {
    cy.get("input[placeholder='Type your message...']").type("Testing{enter}");
    cy.get(".animate-pulse").should("exist"); // typing dots
  });

  it("shows bot reply after API response", () => {
    cy.get("input[placeholder='Type your message...']").type("Hi bot{enter}");
    cy.wait("@chatApi");
    cy.contains("Hello from bot!").should("be.visible");
  });

  it("creates a new chat tab", () => {
    cy.get("input[placeholder='Type your message...']").type("First chat{enter}");
    cy.wait("@chatApi");

    // Should save to localStorage
    cy.window().then((win) => {
      const chats = JSON.parse(win.localStorage.getItem("chats") || "[]");
      expect(chats.length).to.be.greaterThan(0);
    });
  });

  it("allows switching between chat tabs", () => {
    // Start two chats
    cy.get("input[placeholder='Type your message...']").type("Chat 1{enter}");
    cy.wait("@chatApi");
    cy.get("input[placeholder='Type your message...']").type("Chat 2{enter}");
    cy.wait("@chatApi");

    // Sidebar should have at least 2 chats
    cy.get("aside").within(() => {
      cy.contains("Chat 1").click();
    });
    cy.contains("Chat 1").should("be.visible");

    cy.get("aside").within(() => {
      cy.contains("Chat 2").click();
    });
    cy.contains("Chat 2").should("be.visible");
  });
});
