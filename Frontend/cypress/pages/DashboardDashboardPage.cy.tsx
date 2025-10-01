import React from "react";
import { mount } from "cypress/react";
import { MemoryRouter } from "react-router-dom";
import DashboardPage from "../../src/pages/Dashboard";
import supabase from "../../src/config/supabaseClient"; // ✅ import directly

describe("<DashboardPage />", () => {
  beforeEach(() => {
    // Stub supabase.from().select()
    cy.stub(supabase, "from").callsFake((table: string) => {
      return {
        select: () => {
          if (table === "users") {
            return Promise.resolve({
              data: [
                { id: 1, name: "Alice", email: "alice@test.com" },
                { id: 2, name: "Bob", email: "bob@test.com" },
              ],
              error: null,
            });
          } else if (table === "songs") {
            return Promise.resolve({
              data: [],
              error: null,
            });
          } else if (table === "orders") {
            return Promise.resolve({
              data: null,
              error: { message: "DB error" },
            });
          }
          return Promise.resolve({ data: [], error: null });
        },
      };
    });

    mount(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );
  });

  it("renders the dashboard title", () => {
    cy.contains("📊 Dashboard").should("be.visible");
  });

  it("shows table selection buttons", () => {
    cy.contains("users").should("exist");
    cy.contains("songs").should("exist");
    cy.contains("orders").should("exist");
  });

  it("loads and displays rows when clicking 'users'", () => {
    cy.contains("users").click();
    cy.contains("📂 users").should("be.visible");
    cy.contains("Alice").should("be.visible");
    cy.contains("bob@test.com").should("be.visible");
  });

  it("shows 'No data found' when table has no rows", () => {
    cy.contains("songs").click();
    cy.contains("📂 songs").should("be.visible");
    cy.contains("No data found").should("be.visible");
  });

  it("handles errors gracefully", () => {
    cy.contains("orders").click();
    cy.contains("📂 orders").should("be.visible");
    cy.contains("No data found").should("be.visible");
  });
});
