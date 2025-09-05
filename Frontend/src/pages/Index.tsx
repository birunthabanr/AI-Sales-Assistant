import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import supabase from "../config/supabaseClient";

const Index = () => {
  const navigate = useNavigate();
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    // Get existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session?.user) {
        localStorage.setItem("client_id", session.user.id);
      }
    });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);

        if (session?.user) {
          localStorage.setItem("client_id", session.user.id);

          const { id, email, user_metadata } = session.user;
          const clientName = user_metadata?.full_name || email.split("@")[0];

          // Insert client if not exists
          const { error } = await supabase.from("client").upsert(
            {
              client_id: id, 
              client_name: clientName,
              company_id: null,
            },
            { onConflict: "client_id" }
          );

          if (error) console.error("Error creating client:", error);

          // Redirect to chat
          navigate("/chat");
        }
      }
    );

    return () => {
      subscription?.unsubscribe();
    };
  }, [navigate]);

  // Google OAuth
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
    });
    if (error) console.error("Google login error:", error);
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white/90 backdrop-blur-md shadow-xl rounded-2xl p-10 max-w-md w-full text-center space-y-6">
        <h1 className="text-4xl font-extrabold text-gray-900">
          Welcome to <span className="text-indigo-600">ChatApp</span>
        </h1>
        <p className="text-lg text-gray-600">
          Chat, schedule events, and manage your profile all in one place!
        </p>

        <div className="pt-4">
          {session ? (
            <Button
              className="w-full rounded-xl bg-green-600 hover:bg-green-700 text-white text-lg py-6"
              onClick={() => navigate("/chat")}
            >
              Go to Chat
            </Button>
          ) : (
            <Button
              className="w-full rounded-xl bg-red-600 hover:bg-red-700 text-white text-lg py-6"
              onClick={handleGoogleLogin}
            >
              Continue with Google
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
