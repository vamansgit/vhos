import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AuthProvider } from "@/state/auth";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import Dashboard from "@/pages/Dashboard";
import InfluencerDirectory from "@/pages/InfluencerDirectory";
import CampaignList from "@/pages/CampaignList";
import CampaignBriefBuilder from "@/pages/CampaignBriefBuilder";
import CampaignDetail from "@/pages/CampaignDetail";
import ContentStudio from "@/pages/ContentStudio";
import Budget from "@/pages/Budget";
import Settings from "@/pages/Settings";

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
            <Route path="/" element={<Dashboard />} />
            <Route path="/influencers" element={<InfluencerDirectory />} />
            <Route path="/campaigns" element={<CampaignList />} />
            <Route path="/campaigns/new" element={<CampaignBriefBuilder />} />
            <Route path="/campaigns/:id" element={<CampaignDetail />} />
            <Route path="/content" element={<ContentStudio />} />
            <Route path="/budget" element={<Budget />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
