import {
  createContext, useCallback, useContext, useEffect, useRef, useState,
} from "react";
import { CheckCircle2, Info, AlertTriangle, XCircle, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";          // npm i framer-motion
import clsx from "clsx";

const CTX = createContext(null);
export const useNotify = () => useContext(CTX);

const palette = {
  success: "from-emerald-500 to-emerald-600",
  info:    "from-sky-500     to-sky-600",
  warn:    "from-amber-500   to-amber-600",
  error:   "from-rose-500    to-rose-600",
};

const icons = {
  success: CheckCircle2,
  info:    Info,
  warn:    AlertTriangle,
  error:   XCircle,
};

export function NotificationsProvider({ children }) {
  const [list, set] = useState([]);
  const ids = useRef(new Set());

  const push = useCallback((type, text) => {
    const key = `${type}-${text}`;
    if (ids.current.has(key)) return;

    ids.current.add(key);
    const id = Date.now() + Math.random();
    set((prev) => [...prev, { id, type, text }]);
    setTimeout(() => close(id), 5000);
  }, []);

  const close = useCallback((id) => {
    set((prev) => prev.filter((n) => n.id !== id));
    const item = list.find((n) => n.id === id);
    if (item) ids.current.delete(`${item.type}-${item.text}`);
  }, [list]);

  window.toast = push;

  return (
    <CTX.Provider value={{ notify: push }}>
      {children}

      <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3">
        <AnimatePresence>
          {list.map(({ id, type, text }) => {
            const Icon = icons[type] ?? Info;
            return (
              <motion.div
                key={id}
                initial={{ x: 350, opacity: 0 }}
                animate={{ x: 0,   opacity: 1 }}
                exit={{   x: 350, opacity: 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
                className={clsx(
                  "relative w-[300px] sm:w-[340px] text-white overflow-hidden rounded-xl shadow-lg ring-1 ring-black/15",
                  "before:absolute before:inset-0 before:bg-gradient-to-br before:opacity-90",
                  palette[type],
                )}
              >
                <div className="relative flex items-start gap-3 p-4">
                  <Icon size={22} className="shrink-0 mt-0.5" />
                  <span className="text-sm leading-snug">{text}</span>
                  <button
                    onClick={() => close(id)}
                    className="absolute right-2 top-2 p-1 rounded-full hover:bg-white/10"
                  >
                    <X size={18} />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </CTX.Provider>
  );
}
