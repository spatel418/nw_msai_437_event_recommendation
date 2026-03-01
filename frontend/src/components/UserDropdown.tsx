import { useEffect, useRef, useState } from "react";
import { getUsers } from "../api/client";

interface Props {
  onSelect: (userId: string) => void;
}

export default function UserDropdown({ onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await getUsers(search, 50, 0);
        setUsers(res.users.map((u) => u.user_id));
        setTotal(res.total);
      } catch {
        setUsers([]);
      }
      setLoading(false);
    }, 300);
  }, [search]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <input
        type="text"
        placeholder="Search users by ID..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        className="w-full bg-gray-800 border border-gray-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500"
      />
      {open && (
        <div className="absolute z-10 mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-2 text-gray-500 text-sm">Loading...</div>
          ) : users.length === 0 ? (
            <div className="px-4 py-2 text-gray-500 text-sm">No users found</div>
          ) : (
            <>
              <div className="px-4 py-1 text-gray-500 text-xs border-b border-gray-700">
                {total} users found
              </div>
              {users.map((uid) => (
                <button
                  key={uid}
                  onClick={() => {
                    onSelect(uid);
                    setSearch(uid);
                    setOpen(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                >
                  {uid}
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
