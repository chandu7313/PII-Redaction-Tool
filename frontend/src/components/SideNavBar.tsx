import { NavLink, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/', label: 'DOSSIER', icon: 'description' },
  { path: '/archive', label: 'ARCHIVE', icon: 'inventory_2' },
  { path: '/evidence', label: 'EVIDENCE LOG', icon: 'menu_book' },
  { path: '/settings', label: 'SETTINGS', icon: 'settings' },
];

export default function SideNavBar() {
  const location = useLocation();

  // Determine active section from current path
  const isRedactionFlow =
    location.pathname.startsWith('/redaction') ||
    location.pathname.startsWith('/release') ||
    location.pathname.startsWith('/report');

  return (
    <nav className="hidden md:flex flex-col h-full w-64 border-r-2 border-ink bg-surface-container shrink-0 z-10">
      {/* Header / Agency Seal */}
      <div className="p-gutter border-b border-outline-variant flex flex-col items-center justify-center text-center">
        <div className="w-14 h-14 border-2 border-ink flex items-center justify-center mb-3 bg-surface-bright">
          <span className="material-symbols-outlined text-3xl text-ink">gavel</span>
        </div>
        <h1 className="font-headline text-headline-md text-ink uppercase">
          STATION-X
        </h1>
        <p className="font-label text-label-caps text-on-surface-variant uppercase mt-2">
          CLEARANCE LEVEL: TOP SECRET
        </p>
      </div>

      {/* New Case File button */}
      <div className="px-4 py-4 border-b border-outline-variant">
        <NavLink
          to="/"
          className="w-full border-2 border-ink py-2 px-4 font-label text-label-caps font-bold hover:bg-surface-variant transition-colors flex items-center justify-center gap-2 uppercase bg-surface-bright"
        >
          <span className="material-symbols-outlined text-lg">add</span>
          NEW CASE FILE
        </NavLink>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto py-stack">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/' || isRedactionFlow
                : location.pathname === item.path;

            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={`
                    flex items-center gap-4 px-4 py-2 mx-2 my-1
                    font-label text-label-caps uppercase transition-all
                    ${
                      isActive
                        ? 'bg-ink text-on-primary border-2 border-ink font-bold'
                        : 'text-on-surface-variant border border-transparent hover:border-outline hover:bg-surface-variant'
                    }
                  `}
                  style={isActive ? { transform: 'rotate(-1deg)' } : undefined}
                >
                  <span className="material-symbols-outlined">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Footer */}
      <div className="p-stack border-t border-outline-variant">
        <a
          href="#"
          className="flex items-center gap-4 px-4 py-2 mx-2 text-on-surface-variant font-label text-label-caps uppercase hover:bg-surface-variant transition-colors"
        >
          <span className="material-symbols-outlined">logout</span>
          <span>LOGOUT</span>
        </a>
      </div>
    </nav>
  );
}
