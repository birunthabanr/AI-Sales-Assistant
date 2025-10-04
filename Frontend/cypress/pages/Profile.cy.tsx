// cypress/component/Profile.cy.tsx
import React from "react";
import Profile from "../../src/pages/Profile";
import { mount } from "cypress/react";
import { MemoryRouter } from "react-router-dom";



describe("<Profile />", () => {
  beforeEach(() => {
    localStorage.setItem("user_id", "user123");
  });

  it("renders profile header", () => {
    mount(
      <MemoryRouter>
        <Profile />
      </MemoryRouter>
    );

    cy.contains("User Profile").should("be.visible");
    cy.contains("Alice Doe").should("be.visible");
  });

  it("shows chat count", () => {
    mount(
      <MemoryRouter>
        <Profile />
      </MemoryRouter>
    );

    cy.contains("Chats").should("be.visible");
    cy.contains("1").should("be.visible");
  });

  it("allows name change", () => {
    mount(
      <MemoryRouter>
        <Profile />
      </MemoryRouter>
    );

    cy.get("input[placeholder='New Name']").type("New Alice");
    cy.contains("Update Name").click();
    cy.contains("Alice Doe").should("exist"); // original mock data
  });
});
