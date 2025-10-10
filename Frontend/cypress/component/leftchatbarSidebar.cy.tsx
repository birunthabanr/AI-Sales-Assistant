import React from "react";
import { mount } from "cypress/react";
import { MemoryRouter } from "react-router-dom";
import Sidebar from "@/components/leftchatbar";

describe("<Sidebar />", () => {
  const chats = [
    { id: 1, tab: "Chat with Alice", content: [] },
    { id: 2, tab: "Chat with Bob", content: [] },
  ];

  it("renders closed by default", () => {
    const spy = cy.spy().as("sendSpy");
    mount(
      <MemoryRouter>
        <Sidebar chats={chats} activeChatId={1} send_id_to_chat={spy} />
      </MemoryRouter>
    );

    // Select sidebar root div using both classes
    cy.get("div.flex.flex-col").should("have.class", "w-16");
  });

  it("toggles open and close", () => {
    const spy = cy.spy().as("sendSpy");
    mount(
      <MemoryRouter>
        <Sidebar chats={chats} activeChatId={1} send_id_to_chat={spy} />
      </MemoryRouter>
    );

    // Find the toggle button by its text content (usually > or <)
    cy.get("button")
      .contains(/^>$/) // Adjust if your toggle button shows ">" when closed
      .click();

    cy.get("div.flex.flex-col").should("have.class", "w-64");

    cy.get("button")
      .contains(/^<$/) // Adjust if your toggle button shows "<" when open
      .click();

    cy.get("div.flex.flex-col").should("have.class", "w-16");
  });

  it("clicking New Chat calls send_id_to_chat(0)", () => {
    const spy = cy.spy().as("sendSpy");
    mount(
      <MemoryRouter>
        <Sidebar chats={chats} activeChatId={null} send_id_to_chat={spy} />
      </MemoryRouter>
    );

    // Use regex for exact match
    cy.contains("button", /^New Chat$/).click({ force: true });
    cy.get("@sendSpy").should("have.been.calledWith", 0);
  });

  it("clicking a chat calls send_id_to_chat(id)", () => {
    const spy = cy.spy().as("sendSpy");
    mount(
      <MemoryRouter>
        <Sidebar chats={chats} activeChatId={null} send_id_to_chat={spy} />
      </MemoryRouter>
    );

    cy.contains("button", /^Chat with Bob$/).click({ force: true });
    cy.get("@sendSpy").should("have.been.calledWith", 2);
  });

  it("highlights the active chat", () => {
    const spy = cy.spy().as("sendSpy");
    mount(
      <MemoryRouter>
        <Sidebar chats={chats} activeChatId={2} send_id_to_chat={spy} />
      </MemoryRouter>
    );

    cy.contains("button", /^Chat with Bob$/).should(
      "have.class",
      "bg-gray-800"
    );
  });
});
