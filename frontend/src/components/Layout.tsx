import { Outlet, NavLink, useLocation } from 'react-router-dom';
import SideNavBar from './SideNavBar';

export default function Layout() {
  const location = useLocation();

  // Mobile nav items
  const mobileNavItems = [
    { path: '/', label: 'DOSSIER', icon: 'description' },
    { path: '/archive', label: 'ARCHIVE', icon: 'inventory_2' },
    { path: '/evidence', label: 'LOG', icon: 'menu_book' },
    { path: '/settings', label: 'SETTINGS', icon: 'settings' },
  ];

  const isRedactionFlow =
    location.pathname.startsWith('/redaction') ||
    location.pathname.startsWith('/release') ||
    location.pathname.startsWith('/report');

  return (
    <div className="flex h-screen overflow-hidden bg-manila font-body text-on-surface">
      {/* Desktop Side Nav */}
      <SideNavBar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top App Bar */}
        <header className="bg-surface border-b-2 border-ink flex justify-between items-center px-margin py-3 w-full z-30 shrink-0">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-2xl text-ink">folder_open</span>
            <h1 className="font-headline text-headline-md md:text-headline-lg text-ink tracking-tighter uppercase hidden sm:block">
              CASE-FILE REDACTION SYSTEM
            </h1>
            <h1 className="font-headline text-label-caps text-ink tracking-tighter uppercase sm:hidden">
              REDACTION SYS
            </h1>
          </div>

          {/* Desktop nav links */}
          <div className="hidden lg:flex gap-6 font-label text-label-caps uppercase">
            {mobileNavItems.map((item) => {
              const isActive =
                item.path === '/'
                  ? location.pathname === '/' || isRedactionFlow
                  : location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`
                    px-2 py-1 transition-colors
                    ${isActive ? 'text-ink underline decoration-2' : 'text-on-surface-variant hover:bg-surface-container-high'}
                  `}
                >
                  {item.label}
                </NavLink>
              );
            })}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>

        {/* Mobile Bottom Nav */}
        <nav className="md:hidden flex border-t-2 border-ink bg-surface-container shrink-0">
          {mobileNavItems.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/' || isRedactionFlow
                : location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`
                  flex-1 flex flex-col items-center py-2 gap-1
                  font-label text-[10px] uppercase transition-colors
                  ${isActive ? 'text-ink bg-surface-variant' : 'text-on-surface-variant'}
                `}
              >
                <span className="material-symbols-outlined text-lg">{item.icon}</span>
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
