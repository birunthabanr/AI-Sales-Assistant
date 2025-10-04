import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Navigation from "../src/components/Navigation";

// Mock lucide-react icons to simplify tests
jest.mock("lucide-react", () => ({
  MessageCircle: () => <div data-testid="icon-chat" />,
  Calendar: () => <div data-testid="icon-calendar" />,
  User: () => <div data-testid="icon-user" />,
  LogOut: () => <div data-testid="icon-logout" />,
}));

describe("Navigation Component", () => {
  it("renders all navigation items with icons", () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <Navigation />
      </MemoryRouter>
    );

    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();

    expect(screen.getByTestId("icon-chat")).toBeInTheDocument();
    expect(screen.getByTestId("icon-user")).toBeInTheDocument();
    expect(screen.getByTestId("icon-calendar")).toBeInTheDocument();
    expect(screen.getByTestId("icon-logout")).toBeInTheDocument();
  });

  it("highlights the active route", () => {
    render(
      <MemoryRouter initialEntries={["/profile"]}>
        <Navigation />
      </MemoryRouter>
    );

    const profileButton = screen.getByText("Profile").closest("button");
    expect(profileButton).toHaveClass("scale-105");
  });

  it("navigates to the correct route on click", () => {
    const mockNavigate = jest.fn();
    jest.mock("react-router-dom", () => ({
      ...jest.requireActual("react-router-dom"),
      useNavigate: () => mockNavigate,
    }));

    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <Navigation />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("Dashboard"));
    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  });

  it("calls navigate('/') on logout", () => {
    const mockNavigate = jest.fn();
    jest.mock("react-router-dom", () => ({
      ...jest.requireActual("react-router-dom"),
      useNavigate: () => mockNavigate,
    }));

    render(
      <MemoryRouter>
        <Navigation />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("Logout"));
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });
});
