import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import supabase from "../config/supabaseClient";
import { Card, CardContent } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import AnimatedBackground from "@/components/AnimationBackground";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// Types
interface Restaurant {
  id: number;
  name: string;
  cusine_type: string;
  location: string;
  rating: number;
  price_range: string;
  available_slots: number;
  created_at: string;
}

interface Customer {
  customerid: number;
  full_name: string;
  address: string;
  photo: string;
  dob: string;
}

const DashboardPage = () => {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const { data: restaurantData , error} = await supabase
        .from("restaurants")
        .select("*");
      console.log(error)
      const { data: customerData } = await supabase.from("customer").select("*");
      console.log(restaurantData)
      console.log(customerData)
      if (restaurantData) setRestaurants(restaurantData);
      if (customerData) setCustomers(customerData);
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950 text-gray-100">
        <Loader2 className="h-10 w-10 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-violet-950 text-gray-100">
      <AnimatedBackground/>
  <Navigation />
    <div className="min-h-screen bg-gradient-to-b from-indigo-950 via-purple-900 to-violet-950 text-gray-100 p-8">
      <h1 className="text-3xl font-extrabold text-center mb-8">
        📊 Dashboard
      </h1>

      {/* Two-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Restaurants Table */}
        <Card className="shadow-2xl rounded-2xl border border-indigo-950 bg-purple-900">
          <CardContent>
            <h2 className="text-xl font-bold mb-4 text-blue-400">
              🍽️ Restaurants
            </h2>
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-800">
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Cuisine</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Rating</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Slots</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {restaurants.map((r) => (
                  <TableRow
                    key={r.id}
                    className="hover:bg-gray-800 transition"
                  >
                    <TableCell>{r.id}</TableCell>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.cusine_type}</TableCell>
                    <TableCell>{r.location}</TableCell>
                    <TableCell>{r.rating}</TableCell>
                    <TableCell>{r.price_range}</TableCell>
                    <TableCell>{r.available_slots}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Customers Table */}
        <Card className="shadow-2xl rounded-2xl border border-indigo-950 bg-purple-900">
          <CardContent>
            <h2 className="text-xl font-bold mb-4 text-green-400">
              👤 Customers
            </h2>
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-800">
                  <TableHead>ID</TableHead>
                  <TableHead>Photo</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead>DOB</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customers.map((c) => (
                  <TableRow
                    key={c.customerid}
                    className="hover:bg-gray-800 transition"
                  >
                    <TableCell>{c.customerid}</TableCell>
                    <TableCell>
                      <img
                        src={c.photo}
                        alt={c.full_name}
                        className="h-10 w-10 rounded-full object-cover border border-gray-700"
                      />
                    </TableCell>
                    <TableCell>{c.full_name}</TableCell>
                    <TableCell>{c.address}</TableCell>
                    <TableCell>
                      {new Date(c.dob).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
</div>
  );
};

export default DashboardPage;
