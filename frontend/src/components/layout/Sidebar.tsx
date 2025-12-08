import React from 'react';
import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/scan', label: 'Network Scan', icon: '🔍' },
  { to: '/scenarios', label: 'Scenarios', icon: '📚' },
  { to: '/community', label: 'Community', icon: '🌐' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar() {
  return (
    <nav className={styles.sidebar} role="navigation" aria-label="Main navigation">
      <ul className={styles.navList}>
        {navItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.active : ''}`
              }
            >
              <span className={styles.icon} aria-hidden="true">
                {item.icon}
              </span>
              <span className={styles.label}>{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default Sidebar;
