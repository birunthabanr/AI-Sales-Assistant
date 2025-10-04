// cypress/component/Index.cy.tsx
import React from "react";
import Index from "../../src/pages/Index";
import { mount } from "cypress/react";
import { MemoryRouter } from "react-router-dom";


describe("<Index />", () => {
  it("renders welcome text", () => {
    mount(
      <MemoryRouter>
        <Index />
      </MemoryRouter>
    );

    cy.contains("Welcome to ChatApp").should("be.visible");
  });

  it("shows Google login button if no session", () => {
    mount(
      <MemoryRouter>
        <Index />
      </MemoryRouter>
    );

    cy.contains("Continue with Google").should("be.visible");
  });

});
