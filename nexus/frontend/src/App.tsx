import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AuthProvider } from "@/state/auth";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import Chat from "@/pages/Chat";
import Onboard from "@/pages/Onboard";
import SourceList from "@/pages/SourceList";
import SourceDetail from "@/pages/SourceDetail";
import Sell from "@/pages/Sell";
import Finance from "@/pages/Finance";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Chat />} />
            <Route path="/onboard" element={<Onboard />} />
            <Route path="/source" element={<SourceList />} />
            <Route path="/source/:id" element={<SourceDetail />} />
            <Route path="/sell" element={<Sell />} />
            <Route path="/finance" element={<Finance />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
