import { useEffect, useState } from "react";
import supabase from "../config/supabaseClient";

export const useAuthListener = () => {
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      console.log(session)
      setSession(session);
    });

    // Listen for changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);

        if (event === "SIGNED_IN" && session?.user) {
          await createUserIfNotExists(session.user);
          console.log(session.user.id)
          localStorage.setItem("user_id", session.user.id);
        }

        if (event === "SIGNED_OUT") {
          localStorage.removeItem("user_id");
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  return { session };
};

export const createUserIfNotExists = async (user: any) => {
  const { data: existingUser, error: selectError } = await supabase
    .from("users")
    .select("id")
    .eq("id", user.id)
    .maybeSingle(); // better than single()

  if (selectError) {
    console.error("Error checking User:", selectError.message);
    return;
  }

  if (!existingUser) {
    const { error: insertError } = await supabase.from("users").insert({
      id: user.id,
      name: user.user_metadata?.full_name || "",
      email: user.email,
      chat: [],
    });

    if (insertError) console.error("Error inserting User:", insertError.message);
  }
};
