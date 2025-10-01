import React from "react";
import { mount } from "cypress/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Index from "../../src/pages/Index"; // adjust path

describe("<Index />", () => {
  it("renders", () => {
    mount(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Index />} />
        </Routes>
      </MemoryRouter>
    );
  });
});
