import React from "react";
import AnimatedBackground from "../../src/components/AnimationBackground";
import { mount } from "cypress/react";
import { MemoryRouter } from "react-router-dom";

describe("<AnimatedBackground />", () => {
  beforeEach(() => {
    mount(
      <MemoryRouter>
        <AnimatedBackground />
      </MemoryRouter>
    );
  });

  it("renders the component without crashing", () => {
    cy.get(".bubble").should("exist");
    cy.get(".dust").should("exist");
  });

  it("renders around 20 bubbles initially", () => {
    cy.get(".bubble").should("have.length", 20);
  });

  it("renders around 35 dust particles initially", () => {
    cy.get(".dust").should("have.length", 35);
  });

  it("renders extra floating highlights", () => {
    cy.get("[class*='absolute']").filter("div").should("exist");
  });

  it("regenerates bubbles after interval", () => {
    // wait slightly longer than 12s interval to allow regeneration
    cy.wait(12500);
    cy.get(".bubble").should("have.length", 20);
  });

  it("regenerates dust after interval", () => {
    // wait slightly longer than 15s interval
    cy.wait(15500);
    cy.get(".dust").should("have.length", 35);
  });
});
