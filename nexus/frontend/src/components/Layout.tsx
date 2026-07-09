import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/state/auth";
import { titleCase } from "@/lib/format";

const NAV_ITEMS = [
  { to: "/", label: "Chat", end: true },
  { to: "/onboard", label: "Onboard" },
  { to: "/source", label: "Source" },
  { to: "/sell", label: "Sell" },
  { to: "/finance", label: "Finance" },
];

export default function Layout() {
  const { user, brand, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 flex-col border-r border-ink-200 bg-white">
        <div className="flex items-center gap-2 border-b border-ink-200 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            N
          </div>
          <div>
            <div className="text-sm font-semibold text-ink-900">Nexus</div>
            <div className="text-xs text-ink-500">{brand?.name ?? "Loading…"}</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-50 text-brand-700" : "text-ink-600 hover:bg-ink-50"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-ink-200 px-4 py-4">
          <div className="text-sm font-medium text-ink-900">{user?.full_name}</div>
          <div className="text-xs text-ink-500">{user ? titleCase(user.role) : ""}</div>
          <button onClick={logout} className="btn-secondary mt-3 w-full">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto bg-ink-50">
        <Outlet />
      </main>
    </div>
  );
}
