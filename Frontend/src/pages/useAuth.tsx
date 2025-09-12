import { useEffect, useState } from 'react';
import supabase from "../config/supabaseClient";

export const useAuthListener = () => {
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      console.log(session)
      setSession(session);
    });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);
      
      if (event === 'SIGNED_IN' && session?.user) {
        await createUserIfNotExists(session.user);
        
        // Store client_id in localStorage
        localStorage.setItem("user_id", session.user.id);
      }
      
      if (event === 'SIGNED_OUT') {
        localStorage.removeItem("user_id");
      }
    });

    return () => subscription.unsubscribe();
  }, []);
};

// Ensure the user exists in "User" table
export const createUserIfNotExists = async (user: any) => {
  try {
    // 1️⃣ Check if the user already exists
    const { data: existingUser, error: selectError } = await supabase
      .from("User")
      .select("id")
      .eq("id", user.id)   // id must match auth.uid()
      .single();
      console.log(existingUser)
    if (selectError && selectError.code !== "PGRST116") {
      // PGRST116 = "No rows found" is fine
      console.error("Error checking User existence:", selectError.message);
      return;
    }

    if (!existingUser) {
      // 2️⃣ Insert a new row for this user
      const { data: insertData, error: insertError } = await supabase
        .from("User")
        .insert({
          id: user.id,                     // must match auth.uid()
          name: user.user_metadata?.full_name || "",
          email: user.email,
          chat: [],                        // start empty
        });

      if (insertError) {
        console.error("Error creating User record:", insertError.message);
      } else {
        console.log("User created successfully:", insertData);
      }
    }
  } catch (err: any) {
    console.error("Unexpected error in createUserIfNotExists:", err.message);
  }
};

