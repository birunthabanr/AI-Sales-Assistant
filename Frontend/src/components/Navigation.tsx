import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { MessageCircle, Calendar, User, LogOut } from "lucide-react";

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: "/chat", label: "Chat", icon: MessageCircle },
    { path: "/calendar", label: "Calendar", icon: Calendar },
    { path: "/profile", label: "Profile", icon: User },
  ];

  const handleLogout = () => {
    navigate("/login");
  };

  return (
    <nav className="bg-card border-b px-4 py-3">
      <div className="flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.path}
                variant={location.pathname === item.path ? "default" : "ghost"}
                onClick={() => navigate(item.path)}
                className="flex items-center space-x-2"
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Button>
            );
          })}
        </div>
        <Button variant="ghost" onClick={handleLogout} className="flex items-center space-x-2">
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      </div>
    </nav>
  );
};

export default Navigation;