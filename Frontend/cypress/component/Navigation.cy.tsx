// cypress/component/Navigation.cy.jsx

import React from "react"
import Navigation from "../../src/components/Navigation"
import { mount } from "cypress/react"
import { MemoryRouter } from "react-router-dom"
import supabase from "../../src/config/supabaseClient"

describe("<Navigation />", () => {
  beforeEach(() => {
    // CLEAR LOCALSTORAGE BEFORE EACH TEST
    localStorage.clear()
  })

  it("RENDERS DEFAULT NAV ITEMS (CHAT & PROFILE)", () => {
    mount(
      <MemoryRouter>
        <Navigation />
      </MemoryRouter>
    )

    // CHAT AND PROFILE SHOULD BE PRESENT
    cy.contains("Chat").should("exist")
    cy.contains("Profile").should("exist")
  })

  it("HIGHLIGHTS ACTIVE NAV ITEM BASED ON CURRENT ROUTE", () => {
    mount(
      <MemoryRouter initialEntries={["/profile"]}>
        <Navigation />
      </MemoryRouter>
    )

    // PROFILE BUTTON SHOULD HAVE ACTIVE STYLE CLASS
    cy.contains("Profile")
      .should("have.class", "bg-gradient-to-r")
  })

  it("SHOWS DASHBOARD NAV ITEM IF PRIVILEGE IS TRUE", () => {
    // STUB SUPABASE PRIVILEGE RESPONSE
    cy.stub(supabase, "from").returns({
      select: () => ({
        eq: () => ({
          single: () =>
            Promise.resolve({
              data: { privilege: true },
              error: null,
            }),
        }),
      }),
    })

    mount(
      <MemoryRouter>
        <Navigation />
      </MemoryRouter>
    )

    // DASHBOARD LINK SHOULD BE PRESENT
    cy.contains("Dashboard").should("exist")
  })
})
