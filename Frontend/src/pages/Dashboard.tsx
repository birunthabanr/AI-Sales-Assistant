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

// Type for dynamic rows
type Row = Record<string, any>;

const DashboardPage = () => {
  const [tables, setTables] = useState<string[]>([
    "restaurants",
    "artists",
    "bookings",
    "books",
    "creative_works",
    "invoices",
    "newsletter_subscriptions",
    "order_items",
    "orders",
    "payments",
    "playlist_items",
    "playlits",
    "refund_requests",
    "refunds",
    "refunds",
    "resturants",
    "reviews",
    "songs",
    "tickets",
    "users"

    // add more table names or fetch dynamically
  ]);
  const [activeTable, setActiveTable] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);

  // Load data when table changes
  useEffect(() => {
    if (!activeTable) return;
    const fetchData = async () => {
      setLoading(true);
      const { data, error } = await supabase.from(activeTable).select("*");
      if (error) {
        console.error("Error fetching:", error);
        setRows([]);
        setColumns([]);
      } else if (data && data.length > 0) {
        setRows(data);
        setColumns(Object.keys(data[0]));
      } else {
        setRows([]);
        setColumns([]);
      }
      setLoading(false);
    };
    fetchData();
  }, [activeTable]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-gray-100">
      <AnimatedBackground />
      <Navigation />
      <div className="p-8">
        <h1 className="text-3xl font-extrabold text-center mb-8">
          📊 Dashboard
        </h1>

        {/* Table Name List */}
        <div className="flex flex-wrap justify-center gap-4 mb-8">
          {tables.map((t) => (
            <button
              key={t}
              onClick={() => setActiveTable(t)}
              className={`px-4 py-2 rounded-xl font-bold transition shadow-md 
                ${
                  activeTable === t
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Table Viewer */}
        {activeTable && (
          <Card className="shadow-2xl rounded-2xl border border-indigo-950 bg-purple-900">
            <CardContent>
              <h2 className="text-xl font-bold mb-4 text-blue-400">
                📂 {activeTable}
              </h2>

              {loading ? (
                <div className="flex justify-center items-center h-40">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
                </div>
              ) : rows.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-800">
                      {columns.map((col) => (
                        <TableHead key={col}>{col}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row, i) => (
                      <TableRow
                        key={i}
                        className="hover:bg-gray-800 transition"
                      >
                        {columns.map((col) => (
                          <TableCell key={col}>
                            {typeof row[col] === "string" ||
                            typeof row[col] === "number"
                              ? row[col]
                              : JSON.stringify(row[col])}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-gray-400">No data found</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
