import { useEffect, useState } from 'react';
import supabase from "../config/supabaseClient";

export const useAuthListener = () => {
  const [session, setSession] = useState<any>(null);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);
      
      if (event === 'SIGNED_IN' && session?.user) {
        await createClientIfNotExists(session.user);
        
        // Store client_id in localStorage
        localStorage.setItem("client_id", session.user.id);
      }
      
      if (event === 'SIGNED_OUT') {
        localStorage.removeItem("client_id");
      }
    });

    return () => subscription.unsubscribe();
  }, []);
};

const createClientIfNotExists = async (user: any) => {
  try {
    // Check if client already exists
    const { data: existingClient, error: checkError } = await supabase
      .from('client')
      .select('client_id')
      .eq('client_id', user.id)
      .maybeSingle(); // Use maybeSingle instead of single to avoid throwing error if no record found

    if (checkError) {
      console.error('Error checking client existence:', checkError);
      return;
    }

    // If client doesn't exist, create new one
    if (!existingClient) {
      const { error: insertError } = await supabase
        .from('client')
        .insert({
          client_id: user.id,
          client_name: user.user_metadata?.full_name || 
                      user.user_metadata?.name || 
                      user.email?.split('@')[0] || 
                      'Unknown User',
          company_id: null,
          client_chat: [],
          created_at: new Date().toISOString(),
        });

      if (insertError) {
        console.error('Error creating client:', insertError);
      } else {
        console.log('New client created successfully');
      }
    }
  } catch (error) {
    console.error('Error in createClientIfNotExists:', error);
  }
};