import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();

  const linkClass = (path: string) =>
    `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
      pathname === path
        ? "bg-indigo-600 text-white"
        : "text-gray-300 hover:bg-gray-700 hover:text-white"
    }`;

  return (
    <nav className="bg-gray-900 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <span className="text-white text-lg font-bold">Event Recommender</span>
          </div>
          <div className="flex gap-2">
            <Link to="/" className={linkClass("/")}>
              Discover Events
            </Link>
            <Link to="/admin" className={linkClass("/admin")}>
              Admin
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
